from bs4 import BeautifulSoup  # type: ignore
from dotenv import load_dotenv
from grobid_client.grobid_client import GrobidClient  # type: ignore
from langchain.schema.document import Document
from langchain.text_splitter import SpacyTextSplitter
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.vectorstores import VectorStore
from typing import Literal
from typing import List, Union
import arxiv  # type: ignore
import chromadb
import fitz  # type: ignore
import logging
import os
import re
import time

logger_index_new_arxiv_papers = logging.getLogger("IndexNewArxivPapers")
logger_index_new_arxiv_papers.setLevel(logging.INFO)

logger_process_pdf = logging.getLogger("ProcessPDF")
logger_process_pdf.setLevel(logging.INFO)


try:
    load_dotenv()
except:
    pass


def read_tei(tei_file):
    """
    Read and parse a TEI file.

    :param tei_file: The path to the TEI file.
    :type tei_file: str
    :return: The parsed TEI file as a BeautifulSoup object.
    :rtype: BeautifulSoup
    :raises RuntimeError: If the TEI file cannot be parsed.
    """
    with open(
        tei_file, "r", encoding="utf-8"
    ) as tei:  # Open the TEI file with 'ISO-8859-1' encoding
        soup = BeautifulSoup(tei, "lxml-xml")
        return soup
    raise RuntimeError("Cannot generate a soup from the input")


def elem_to_text(elem, default=""):
    """
    Convert an element to text.

    :param elem: The element to convert.
    :type elem: bs4.element.Tag or None
    :param default: The default value to return if the element is None.
    :type default: str

    :return: The text representation of the element, or the default value if the element is None.
    :rtype: str
    """
    if elem:
        return elem.getText()
    else:
        return default


class TEIFile(object):
    """Class representing a TEI file.

    :param filename: The path to the TEI file.
    :type filename: str

    :ivar filename: The path to the TEI file.
    :vartype filename: str
    :ivar soup: The BeautifulSoup object representing the TEI file.
    :vartype soup: BeautifulSoup
    :ivar doi: The DOI of the TEI file.
    :vartype doi: str
    :ivar title: The title of the TEI file.
    :vartype title: str
    :ivar published: The publication date of the TEI file.
    :vartype published: str
    :ivar abstract: The abstract of the TEI file.
    :vartype abstract: str
    :ivar authors: The authors of the TEI file.
    :vartype authors: List[str]
    :ivar text: The plain text content of the TEI file.
    :vartype text: str
    """

    def __init__(self, filename):
        """
        Constructor for TEIFile object.
        """
        self.filename = filename
        self.soup = read_tei(filename)
        self._title = None
        self._abstract = None
        self._text = None

    @property
    def doi(self) -> str:
        """
        Get the DOI of the TEI file.

        :return: The DOI string.
        :rtype: str
        """
        idno_elem = self.soup.find("idno", type="DOI")
        if not idno_elem:
            return ""
        else:
            return idno_elem.getText()

    @property
    def title(self) -> str:
        """
        Get the title of the TEI file.

        :return: The title string.
        :rtype: str
        """
        if not self._title:
            self._title = self.soup.title.getText()
        return self._title

    @property
    def published(self) -> str:
        """
        Get the publication date of the TEI file.

        :return: The publication date string.
        :rtype: str
        """
        date = self.soup.date.get("when")
        if date:
            return date
        else:
            return ""

    @property
    def abstract(self) -> str:
        """
        Get the abstract of the TEI file.

        :return: The abstract string.
        :rtype: str
        """
        if not self._abstract:
            abstract = self.soup.abstract.getText(separator=" ", strip=True)
            self._abstract = abstract
        return self._abstract

    @property
    def authors(self) -> List[str]:
        """
        Get the authors of the TEI file.

        :return: A list of author names.
        :rtype: List[str]
        """
        authors_in_header = self.soup.analytic.find_all("author")

        result = []
        for author in authors_in_header:
            firstname = elem_to_text(author.find("forename", type="first")).strip()
            middlename = elem_to_text(author.find("forename", type="middle")).strip()
            surname = elem_to_text(author.surname).strip()
            if middlename == "":
                full_name = f"{firstname} {surname}".strip()
            else:
                full_name = f"{firstname} {middlename} {surname}".strip()
            result.append(full_name)
        return result

    @property
    def text(self) -> str:
        """
        Get the plain text content of the TEI file.

        :return: The plain text string.
        :rtype: str
        """
        if not self._text:
            divs_text = []
            for div in self.soup.body.find_all("div"):
                # div is neither an appendix nor references, just plain text.
                if not div.get("type"):
                    text = div.getText(separator=": ", strip=True).replace("\n", "")

                    divs_text.append(text)
            plain_text = "\n\n".join(divs_text)
            self._text = plain_text
        return self._text


class PyMuPDFParser:
    """
    A class for parsing PDF files using PyMuPDF library.


    :param pdf_path: The path to the PDF file.
    :type pdf_path: str

    :ivar pdf_path: The path to the PDF file.
    :vartype pdf_path: str
    :ivar doc: The PyMuPDF document object.
    :vartype doc: fitz.Document
    :ivar id: The arXiv ID of the PDF file (if exist).
    :vartype id: str

    :cvar _INTRO_DELIMITERS: The delimiters used to split the introduction from the rest of the content.
    :vartype _INTRO_DELIMITERS: str
    :cvar _REF_DELIMITERS: The delimiters used to split the references from the rest of the content.
    :vartype _REF_DELIMITERS: str
    :cvar _APPENDIX_DELIMITERS: The delimiters used to split the appendix from the rest of the content.
    :vartype _APPENDIX_DELIMITERS: str
    """

    _INTRO_DELIMITERS = "|".join(map(re.escape, ["Introduction\n", "INTRODUCTION\n"]))
    _REF_DELIMITERS = "|".join(map(re.escape, ["References\n", "REFERENCES\n"]))
    _APPENDIX_DELIMITERS = "|".join(map(re.escape, ["Appendix\n", "APPENDIX\n"]))

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(self.pdf_path)
        self.id = self.pdf_path.split("/")[-1].split(".")[0]

    def process(self) -> str:
        """
        Process the PDF file and extract the content (text body and appendices).

        :return: The content of the PDF file.
        :rtype: str
        """
        content = ""
        for page in self.doc:
            content += page.get_text()  # type: ignore

        content = re.split(self._INTRO_DELIMITERS, content)[-1]
        content = re.split(self._REF_DELIMITERS, content)[0]
        appendix = re.split(self._APPENDIX_DELIMITERS, content)[-1]
        content += "\n\n" + appendix

        return content


class ProcessPDF:
    """
    Class for processing PDF documents and extracting metadata and content.

    :param vectordb: The vector store used for storing document vectors.
    :type vectordb: VectorStore
    :param parser: The PDF parser to use. Can be either "PyMuPDF" or "GROBID". Defaults to "PyMuPDF".
    :type parser: Literal["PyMuPDF", "GROBID"]
    :param chunk_size: The size of each text chunk in bytes. Defaults to 1024.
    :type chunk_size: int
    :param chunk_overlap: The overlap between consecutive text chunks in bytes. Defaults to 100.
    :type chunk_overlap: int


    :ivar vectordb: The vector store used for storing document vectors.
    :vartype vectordb: VectorStore
    :ivar parser: The PDF parser to use. Can be either "PyMuPDF" or "GROBID". Defaults to "PyMuPDF".
    :vartype parser: Literal["PyMuPDF", "GROBID"]
    :ivar text_splitter: The TextSplitter object from Langchain used to split the text into chunks. Defaults to SpacyTextSplitter.
    :vartype text_splitter: langchain.text_splitter.TextSplitter

    :cvar grobid_client: The GROBID client object.
    :vartype grobid_client: grobid_client.grobid_client.GrobidClient
    """

    def __init__(
        self,
        vectordb: VectorStore,
        parser: Literal["PyMuPDF", "GROBID"] = "PyMuPDF",
        chunk_size: int = 1024,
        chunk_overlap: int = 100,
    ):
        """
        Constructor for the ProcessPDF object.
        """
        self.grobid_client = GrobidClient(
            grobid_server=os.environ.get("GROBID_FQDN"), sleep_time=0, batch_size=10
        )
        self.vectordb = vectordb
        self.parser = parser
        self.text_splitter = SpacyTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator="\n\n"
        )

    def _get_id_from_str(self, string: str) -> str:
        """
        Extract the arXiv ID from a string.

        :param string: The input string.
        :return: The extracted arXiv ID.
        """
        ARXIV_ID_REGEX = r"(\d{4}\.\d{5})(v\d{1})?"
        result = re.findall(ARXIV_ID_REGEX, string)
        if len(result) == 0:
            return string
        else:
            return "".join(result[0])

    def _extract_metadata(self, list_of_files: List[str]) -> List[dict[str, str]]:
        """
        Extract metadata from a PDF document using GROBID.

        :param paper: The path to the PDF document.
        :type paper: str

        :return: A dictionary containing the extracted metadata.
        :rtype: dict
        """
        # filenames = [paper.split("/")[-1].replace('.pdf', '') for paper in list_of_files]
        # entry_ids = [self._get_id_from_str(filename) for filename in filenames]

        files_to_process = []
        for file in list_of_files:
            filename = file.split("/")[-1].replace("pdf", "")
            entry_id = self._get_id_from_str(filename)
            if not os.path.exists(f"./output/{entry_id}.grobid.tei.xml"):
                files_to_process.append(file)
            else:
                continue
        if not files_to_process == []:
            self.grobid_client.process_batch(
                service="processHeaderDocument",
                input_files=files_to_process,
                input_path=os.path.dirname(files_to_process[0]),
                output=f"./output/",
                generateIDs=False,
                n=10,
                consolidate_header=False,
                consolidate_citations=False,
                include_raw_citations=False,
                include_raw_affiliations=False,
                tei_coordinates=False,
                segment_sentences=False,
                force=True,
                verbose=False,
            )
        else:
            pass

        metadatas = []
        for paper in list_of_files:
            filename = paper.split("/")[-1].replace(".pdf", "")
            entry_id = self._get_id_from_str(filename)

            new_path = ""
            if self.parser == "PyMuPDF":
                old_path = f"./output/{entry_id}.grobid.tei.xml"
                new_path = f"./output/{entry_id}.header.grobid.tei.xml"
                os.rename(old_path, new_path)
            elif self.parser == "GROBID":
                new_path = f"./output/{entry_id}.grobid.tei.xml"

            tei_object = TEIFile(new_path)
            metadatas.append(
                {
                    "paper_id": entry_id,
                    "title": tei_object.title,
                    "authors": ", ".join([author for author in tei_object.authors]),
                    "date": tei_object.published,
                    "abstract": tei_object.abstract,
                }
            )
        return metadatas

    def _process_pymupdf(
        self, pdf_path: List[str], metadatas: Union[List[dict[str, str]], None] = None
    ) -> List[Document]:
        """
        Process PDF documents using the PyMuPDF parser. Metadata is extracted using GROBID.

        :param pdf_path: A list of paths to the PDF documents.
        :type pdf_path: List[str]

        :return: A list of Document objects containing the processed content and metadata.
        :rtype: List[Document]
        """

        if not metadatas:
            metadatas = self._extract_metadata(pdf_path)

        docs = []
        for idx, paper in enumerate(pdf_path):
            text = PyMuPDFParser(paper).process()
            chunks = self.text_splitter.split_text(text)
            metadata = metadatas[idx]

            for i, chunk in enumerate(chunks):
                metadata["chunk_id"] = f"{metadata['paper_id']}-{i}"
                docs.append(Document(page_content=chunk, metadata=metadata))
        return docs

    def _process_grobid(
        self, pdf_path: List[str], metadatas: Union[List[dict[str, str]], None] = None
    ) -> List[Document]:
        """
        Process PDF documents using the GROBID parser.

        :param pdf_path: A list of paths to the PDF documents.
        :type pdf_path: List[str]

        :return: A list of Document objects containing the processed content.
        :rtype: List[Document]
        """
        self.grobid_client.process_batch(
            service="processFulltextDocument",
            input_files=pdf_path,
            input_path=os.path.dirname(pdf_path[0]),
            output=f"./output/",
            generateIDs=False,
            n=10,
            consolidate_header=False,
            consolidate_citations=False,
            include_raw_citations=False,
            include_raw_affiliations=False,
            tei_coordinates=False,
            segment_sentences=False,
            force=True,
            verbose=False,
        )

        while not all(
            [
                os.path.exists(
                    f"./output/{paper.split('/')[-1].replace('.pdf', '')}.grobid.tei.xml"
                )
                for paper in pdf_path
            ]
        ):
            time.sleep(1)

        if not metadatas:
            metadatas = self._extract_metadata(pdf_path)

        docs = []
        for idx, paper in enumerate(pdf_path):
            filename = paper.split("/")[-1].replace(".pdf", "")
            id = self._get_id_from_str(filename)
            tei_object = TEIFile(f"./output/{id}.grobid.tei.xml")
            chunks = self.text_splitter.split_text(tei_object.text)
            metadata = metadatas[idx]

            for i, chunk in enumerate(chunks):
                metadata["chunk_id"] = f"{metadata['paper_id']}-{i}"
                docs.append(Document(page_content=chunk, metadata=metadata))

        return docs

    def process(
        self,
        pdf_path: Union[List[str], str],
        metadatas: Union[List[dict[str, str]], None] = None,
    ) -> List[Document]:
        """
        Process PDF documents and add them to the vector store.

        :param pdf_path: Directory of pdf files or a (list of) pdf file(s).
        :type pdf_path: Union[List[str], str]

        :return: A list of Document objects containing the processed content.
        :rtype: List[Document]

        :raises ValueError: If the input is not a list of paths to PDF documents or a directory containing PDF files.
        """
        list_of_files = []
        if isinstance(pdf_path, str):
            if os.path.isdir(pdf_path):
                list_of_files.extend(
                    [f"{pdf_path}/{file}" for file in os.listdir(pdf_path)]
                )
            elif os.path.isfile(pdf_path) and pdf_path.endswith(".pdf"):
                list_of_files.append(pdf_path)
            else:
                raise ValueError(
                    "pdf_path must be a directory of pdf files or a (list of) pdf file(s)."
                )

        if isinstance(pdf_path, list):
            if all([file.endswith(".pdf") for file in pdf_path]):
                list_of_files = pdf_path
            else:
                raise ValueError(
                    "pdf_path must be a directory of pdf files or a (list of) pdf file(s)."
                )

        docs = []
        if self.parser == "PyMuPDF":
            docs = self._process_pymupdf(list_of_files, metadatas)
        if self.parser == "GROBID":
            docs = self._process_grobid(list_of_files, metadatas)

        self.vectordb.add_documents(docs)

        return docs


class IndexNewArxivPapers:
    """
    IndexNewArxivPapers class is responsible for indexing new arXiv papers.

    :param vectordb: The vector store used for indexing.
    :type vectordb: VectorStore
    :param n_search_results: The number of search results to retrieve from Google.
    :type n_search_results: int, optional
    :param pdf_parser: The PDF parser to use. Either "PyMuPDF" or "GROBID".
    :type pdf_parser: Literal["PyMuPDF", "GROBID"], optional
    :param chunk_size: The size of each chunk when processing PDFs.
    :type chunk_size: int, optional
    :param chunk_overlap: The overlap between chunks when processing PDFs.
    :type chunk_overlap: int, optional

    :ivar vectordb: The vector store used for indexing.
    :vartype vectordb: VectorStore
    :ivar n_search_results: The number of search results to retrieve from Google. Defaults to 2.
    :vartype n_search_results: int
    :ivar pdf_parser: The PDF parser to use. Either "PyMuPDF" or "GROBID". Defaults to "PyMuPDF".
    :vartype pdf_parser: Literal["PyMuPDF", "GROBID"]
    :ivar chunk_size: The size of each chunk when processing PDFs. Defaults to 1024.
    :vartype chunk_size: int
    :ivar chunk_overlap: The overlap between chunks when processing PDFs. Defaults to 100.
    :vartype chunk_overlap: int

    :cvar google_api: The GoogleSearchAPIWrapper object.
    :vartype google_api: GoogleSearchAPIWrapper
    :cvar arxiv_client: The arXiv client object.
    :vartype arxiv_client: arxiv.Client
    :cvar chromadb_client: The chromadb client object.
    :vartype chromadb_client: chromadb.PersistentClient
    """

    google_api = GoogleSearchAPIWrapper()
    arxiv_client = arxiv.Client(delay_seconds=0)

    def __init__(
        self,
        vectordb: VectorStore,
        n_search_results: int = 2,
        pdf_parser: Literal["PyMuPDF", "GROBID"] = "PyMuPDF",
        chunk_size: int = 1024,
        chunk_overlap: int = 100,
    ):
        """
        Constructor for the IndexNewArxivPapers object.
        """
        self.vectordb = vectordb
        self.n_search_results = n_search_results
        self.chunk_size = chunk_size
        self.chromadb_client = chromadb.PersistentClient("arxiv_vdb").get_collection(
            "arxiv"
        )
        self.chunk_overlap = chunk_overlap
        self.pdf_parser = pdf_parser

    def _get_paper_ids(self, query: str) -> List[str]:
        """
        Get the arXiv paper IDs from a given query.

        :param query: The search query.
        :type query: str

        :return: The list of arXiv paper IDs.
        :rtype: List[str]

        :raises IndexError: If no papers are found for the given query.
        """
        ARXIV_ID_REGEX = r"\d{4}\.\d{4,5}"
        try:
            ids = list(
                {
                    re.findall(ARXIV_ID_REGEX, result["link"])[0]
                    for result in self.google_api.results(query, self.n_search_results)
                }
            )
        except IndexError:
            raise IndexError("No papers found, try a different query.")

        return ids

    def _run(self, query):
        """
        Run the indexing process for the given query.

        :param query: The search query.
        :type query: str
        :return: The indexed documents.
        :rtype: List[Document]
        """
        # with cl.Step():
        self.ids = self._get_paper_ids(query)
        os.makedirs(f"./output", exist_ok=True)
        os.makedirs(f"./pdfs", exist_ok=True)
        print(self.chromadb_client)

        for id in self.ids:
            if len(self.chromadb_client.get(where={"paper_id": id})["ids"]) > 0:
                self.ids.remove(id)
            else:
                continue

        papers = list(self.arxiv_client.results(arxiv.Search(id_list=self.ids)))
        metadatas = []
        for paper in papers:
            id = paper.entry_id.split("/")[-1]
            paper.download_pdf(dirpath=f"./pdfs/", filename=f"{id}.pdf")
            metadatas.append(
                {
                    "paper_id": id,
                    "title": paper.title,
                    "authors": ", ".join([author.name for author in paper.authors]),
                    "date": paper.published.strftime("%Y-%m-%d"),
                    "abstract": paper.summary,
                }
            )

        while not all(
            [
                os.path.exists(f"./pdfs/{paper.entry_id.split('/')[-1]}.pdf")
                for paper in papers
            ]
        ):
            time.sleep(1)

        pdf_files = [f"./pdfs/{paper.entry_id.split('/')[-1]}.pdf" for paper in papers]
        processor = ProcessPDF(
            vectordb=self.vectordb,
            parser=self.pdf_parser,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        _ = processor.process(pdf_files, metadatas)

    async def _arun(self, query: str):
        return self._run(query)

    # test edit
