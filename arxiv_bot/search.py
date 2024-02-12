from bs4 import BeautifulSoup #type: ignore
from dataclasses import dataclass
from dotenv import load_dotenv
from grobid_client.grobid_client import GrobidClient #type: ignore
from langchain.schema.document import Document
from langchain.text_splitter import SpacyTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.vectorstores import VectorStore
from typing import  Literal
import arxiv #type: ignore
import chainlit as cl
import chromadb
import os
import fitz #type: ignore
import re
import time
from typing import List, Union
import logging

logging.getLogger("IndexNewArxivPapers").setLevel(logging.INFO)
try:
    load_dotenv()
except:
    pass


def read_tei(tei_file):
    with open(tei_file, 'r', encoding='utf-8') as tei: # Open the TEI file with 'ISO-8859-1' encoding
        soup = BeautifulSoup(tei, 'lxml-xml')
        return soup
    raise RuntimeError('Cannot generate a soup from the input')

def elem_to_text(elem, default=''):
    if elem:
        return elem.getText()
    else:
        return default

class TEIFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.soup = read_tei(filename)
        self._text = None
        self._title = ''
        self._abstract = ''

    @property
    def doi(self):
        idno_elem = self.soup.find('idno', type='DOI')
        if not idno_elem:
            return ''
        else:
            return idno_elem.getText()

    @property
    def title(self):
        if not self._title:
            self._title = self.soup.title.getText() #type: ignore
        return self._title

    @property
    def published(self):
        return self.soup.date.get("when")
    
    @property
    def abstract(self):
        if not self._abstract:
            abstract = self.soup.abstract.getText(separator=' ', strip=True) #type: ignore
            self._abstract = abstract
        return self._abstract

    @property
    def authors(self):
        authors_in_header = self.soup.analytic.find_all('author') #type: ignore

        result = []
        for author in authors_in_header:
            firstname = elem_to_text(author.find("forename", type="first")).strip()
            middlename = elem_to_text(author.find("forename", type="middle")).strip()
            surname = elem_to_text(author.surname).strip()
            if middlename == '':
                full_name = f"{firstname} {surname}".strip()
            else:
                full_name = f"{firstname} {middlename} {surname}".strip()
            result.append(full_name)
        return result
    
    @property
    def text(self):
        if not self._text:
            divs_text = []
            for div in self.soup.body.find_all("div"): #type: ignore
                # div is neither an appendix nor references, just plain text.
                if not div.get("type"):
                    text = div.getText(separator=': ', strip=True).replace("\n", "")
                    
                    divs_text.append(text)
            plain_text = "\n\n".join(divs_text)
            self._text = plain_text
        return self._text


class PyMuPDFParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(self.pdf_path)
        self.id = self.pdf_path.split("/")[-1].split(".")[0]
        self._INTRO_DELIMITERS = '|'.join(map(re.escape, ['Introduction\n', 'INTRODUCTION\n']))
        self._REF_DELIMITERS = '|'.join(map(re.escape, ['References\n', 'REFERENCES\n']))
        self._APPENDIX_DELIMITERS = '|'.join(map(re.escape, ['Appendix\n', 'APPENDIX\n']))
        
    def process(self):
        content = ""
        for page in self.doc:
            content += page.get_text() #type: ignore
        
        content = re.split(self._INTRO_DELIMITERS, content)[-1]
        content = re.split(self._REF_DELIMITERS, content)[0]
        appendix = re.split(self._APPENDIX_DELIMITERS, content)[-1]
        content += "\n\n" + appendix
        
        return content
    
class ProcessPDF:
    def __init__(self,
                #  vectordb: VectorStore,
                 parser: Literal["PyMuPDF", "GROBID"] = "PyMuPDF",
                 chunk_size: int = 1024,
                 chunk_overlap: int = 100,
                 ):

        # self.vectordb = vectordb
        self.parser = parser
        self.chunk_size = chunk_size
        self.grobid_client = GrobidClient(config_path="./grobid_client_python/config.json")
        self.chunk_overlap = chunk_overlap
        self.text_splitter = SpacyTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap = chunk_overlap,
            separator="\n\n"
            )
        
    def _get_id_from_str(self, string: str) -> str:
        ARXIV_ID_REGEX =  r"\d{4}\.\d{4,5}"
        result = re.findall(ARXIV_ID_REGEX, string)[0]
        if len(result) == 0:
            return string
        else:
            return result
        
    def _extract_metadata(self, paper: str) -> dict:
        filename = paper.split("/")[-1]
        entry_id = self._get_id_from_str(filename)
        
        old_path = f"./output/{entry_id}.grobid.tei.xml"
        new_path = f"./output/{entry_id}.header.grobid.tei.xml"
        os.rename(old_path, new_path)
        
        tei_object = TEIFile(new_path)
        title = tei_object.title
        authors = ", ".join([author for author in tei_object.authors])
        abstract = tei_object.abstract
        date = tei_object.published
        return {
            'paper_id': entry_id,
            'title': title, 
            'authors': authors,
            'date': date,
            'abstract': abstract
        }
        
    def _process_pymupdf(self, pdf_path: List[str]) -> List[Document]:
        docs = []
        self.grobid_client.process_batch(
            "processHeaderDocument",
            pdf_path,
            input_path = os.path.dirname(pdf_path[0]),
            output=f"./output/",
            generateIDs=False,
            n=10,
            consolidate_header=True,
            consolidate_citations=False,
            include_raw_citations=False,
            include_raw_affiliations=False,
            tei_coordinates=False,
            segment_sentences=False,
            force=False,
            verbose=False,
            )
        
        for paper in pdf_path:                               
            text = PyMuPDFParser(paper).process()
            chunks = self.text_splitter.split_text(text)
            metadata = self._extract_metadata(paper)
            for i, chunk in enumerate(chunks):
                metadata['chunk_id'] = f"{metadata['paper_id']}-{i}"
                docs.append(
                    Document(
                            page_content=chunk, 
                            metadata=metadata
                            )
                        )
        return docs

        
        
    def process(self, pdf_path: Union[List[str], str]):
        list_of_files = []
        if isinstance(pdf_path, str):
            if os.path.isdir(pdf_path):
                list_of_files.extend([f"{pdf_path}/{file}" for file in os.listdir(pdf_path)])
            elif os.path.isfile(pdf_path) and pdf_path.endswith(".pdf"):
                list_of_files.append(pdf_path)
            else:
                raise ValueError("pdf_path must be a directory of pdf files or a (list of) pdf file(s).")
            
        if isinstance(pdf_path, list):
            if all([file.endswith(".pdf") for file in pdf_path]):
                list_of_files = pdf_path
            else:
                raise ValueError("pdf_path must be a directory of pdf files or a (list of) pdf file(s).")
            
        if self.parser == "PyMuPDF":
            return self._process_pymupdf(list_of_files)
            
        
        
class IndexNewArxivPapers:
    """
    This tool indexes new papers from arxiv using the following steps:
    
    1. Get the paper ids from google search
    2. Download the papers
    3. Process the papers with GROBID
    4. Parse the TEI files
    5. Add the papers to the vectorstore
    
    """
    def __init__(self, 
                vectordb: VectorStore,
                n_search_results: int = 2,
                pdf_parser: Literal["PyMuPDF", "GROBID"] = "PyMuPDF",
                chunk_size: int = 1024,
                chunk_overlap: int = 100,
                ):
    
        self.google_api = GoogleSearchAPIWrapper()
        self.arxiv_client = arxiv.Client(delay_seconds=0)
        self.vectordb = vectordb
        self.chromadb_client = chromadb.PersistentClient("arxiv_vdb").get_collection("arxiv")
        self.n_search_results = n_search_results
        self.splitter = SpacyTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap = chunk_overlap,
            separator="\n\n")
        self.pdf_parser = pdf_parser
    
    def _get_paper_ids(self, query: str) -> List[str]:
        ARXIV_ID_REGEX =  r"\d{4}\.\d{4,5}"
        try:
            ids = list(
                {re.findall(ARXIV_ID_REGEX, result['link'])[0] 
                for result in self.google_api.results(query, self.n_search_results)}
                )
        except IndexError:
            raise IndexError("No papers found, try a different query.")
        
        return ids
    
    def _run(self, query):
        with cl.Step():
            self.ids = self._get_paper_ids(query)
            print(self.ids)
            os.makedirs(f"./output/{query}", exist_ok=True)
            os.makedirs(f"./pdfs/{query}", exist_ok=True)
            
            for id in self.ids:
                if len(self.chromadb_client.get(where={'paper_id': id})['ids']) > 0:
                    self.ids.remove(id)
                else:
                    continue
            
            papers = list(self.arxiv_client.results(arxiv.Search(id_list=self.ids)))
            for paper in papers:
                id = paper.entry_id.split('/')[-1]
                paper.download_pdf(dirpath=f"./pdfs/{query}/", filename=f"{paper.entry_id.split('/')[-1]}.pdf")
            
            while not all([os.path.exists(f"./pdfs/{query}/{paper.entry_id.split('/')[-1]}.pdf") for paper in papers]):
                time.sleep(1)
            
            docs = []
            print(self.pdf_parser)
            if self.pdf_parser == "GROBID":
                self.grobid_client = GrobidClient(config_path="./grobid_client_python/config.json")
                self.grobid_client.process("processFulltextDocument", f"./pdfs/{query}/", output=f"./output/{query}", force=True)            
                
                while not all([os.path.exists(f"./output/{query}/{paper.entry_id.split('/')[-1]}.grobid.tei.xml") for paper in papers]):
                    time.sleep(1)
            
                for paper in papers:
                    tei_object = TEIFile(f"./output/{query}/{paper.entry_id.split('/')[-1]}.grobid.tei.xml")
                    chunks = self.splitter.split_text(tei_object.text)
                    docs.extend([
                            Document(
                                    page_content=chunk, 
                                    metadata={
                                        'paper_id': paper.entry_id.split("/")[-1],
                                        'authors': ", ".join([author.name for author in paper.authors]),
                                        'title': paper.title,
                                        'chunk_id': f"{paper.entry_id.split('/')[-1]}-{i}"
                                        }
                                    )
                                    for i, chunk in enumerate(chunks)
                                ]
                            )
                    
            if self.pdf_parser == "PyMuPDF":
                for paper in papers:
                    # loader = PyMuPDFLoader(f"pdfs/{query}/{paper.entry_id.split('/')[-1]}.pdf")
                    # chunks = loader.load_and_split(self.splitter)                    
                    text = PyMuPDFParser(f"./pdfs/{query}/{paper.entry_id.split('/')[-1]}.pdf").process()
                    chunks = self.splitter.split_text(text)
                    docs.extend([
                            Document(
                                    page_content=chunk, 
                                    metadata={
                                        'paper_id': paper.entry_id.split("/")[-1],
                                        'authors': ", ".join([author.name for author in paper.authors]),
                                        'date': paper.published.strftime("%Y-%m-%d"),
                                        'abstract': paper.summary,
                                        'title': paper.title,
                                        'chunk_id': f"{paper.entry_id.split('/')[-1]}-{i}"
                                        }
                                    ) 
                                    for i, chunk in enumerate(chunks)
                                ]
                            )
            self.vectordb.add_documents(docs)


    async def _arun(self, query: str):
        async with cl.Step():
            self._run(query)
            # self.ids = self._get_paper_ids(query)
            
            
            # os.makedirs("./output/", exist_ok=True)
            # os.makedirs("./pdfs/", exist_ok=True)
            
            # docs = []
            # for id in self.ids:
            #     if not len(self.chromadb_client.get(where={'paper_id': id})['ids']) > 0:
            #         paper = list(self.arxiv_client.results(arxiv.Search(id_list=[id])))[0]
            #         paper.download_pdf(dirpath=f"./pdfs/", filename=f"{id}.pdf")
            #         while not os.path.exists(f"./pdfs/{id}.pdf"):
            #             time.sleep(1)
                    
            #         if self.pdf_parser == "grobid":
            #             self.grobid_client = GrobidClient(config_path="./grobid_client_python/config.json")
            #             self.grobid_client.process("processFulltextDocument", f"./pdfs/", output=f"./output/", force=True)            
                        
            #             while not os.path.exists(f"./output/{id}.grobid.tei.xml"):
            #                 time.sleep(1)
                    
            #             tei_object = TEIFile(f"./output/{id}.grobid.tei.xml")
            #             chunks = self.splitter.split_text(tei_object.text)
            #             docs = [
            #                     Document(
            #                             page_content=chunk, 
            #                             metadata={
            #                                 'paper_id': id,
            #                                 'authors': ", ".join(tei_object.authors),
            #                                 'title': paper.title,
            #                                 'chunk_id': f"{id}-{i}"
            #                                 }
            #                             )
            #                             for i, chunk in enumerate(chunks)
            #                         ]
                        

            #         if self.pdf_parser == "pymupdf":
                        
            #             loader = PyMuPDFLoader(f"pdfs/{id}.pdf")
            #             docs = loader.load_and_split(self.splitter)                    
            #             docs = [
            #                 Document(
            #                         page_content=doc.page_content , 
            #                         metadata={
            #                                 'paper_id': id,
            #                                 'authors': ", ".join([author.name for author in paper.authors]),
            #                                 'title': paper.title,
            #                                 'chunk_id': f"{id}-{i}"}
            #                         ) 
            #                         for i, doc in enumerate(docs)
            #                     ]
            
            #         self.vectordb.add_documents(
            #             docs
            #         )

            #     else:
            #         continue        





