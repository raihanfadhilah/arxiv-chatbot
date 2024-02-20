from langchain.schema.document import Document
from langchain.schema.retriever import BaseRetriever
from langchain.tools import BaseTool
from langchain_core.callbacks.manager import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain_core.vectorstores import VectorStore
from langchain_openai.llms import OpenAI
from langchain.chains import LLMChain
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from typing import List, Type, Optional
from arxiv_bot.search import IndexNewArxivPapers
from langchain.pydantic_v1 import BaseModel, Field
import chainlit as cl
from typing import Literal, List
import logging

logging.basicConfig()
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)

class RetrievalInput(BaseModel):
    query: str = Field(title="Query", description="The query to use to find relevant documents.")

# class Retriever(BaseTool):
#     vectordb: VectorStore
#     arg_schema: Optional[Type[BaseModel]] = RetrievalInput
#     name: str = "Retriever"
#     description: str  = "Retriever that find documents from the vectorstore."
    
#     def _run(self, query: str) -> List[Document]:
#         """
#         Get relevant documents by using the vectorstore.
        
#         :param query: The query to use to find relevant documents.
#         :type query: str
#         :param run_manager: The callback manager to use to manage callbacks.
#         :type run_manager: CallbackManagerForRetrieverRun
        
        
#         :return: List of relevant documents.
#         :rtype: List[Document]
        
#         """
#         with cl.Step("retriever", show_input=True) as step:
#             step.input = "Query: " + query
#             documents = self.vectordb.max_marginal_relevance_search(query, k=3, fetch_k=10)
#             retrieved_information = "Retrieved the following documents:\n"
#             for idx, doc in enumerate(documents):
#                 text = doc.page_content
#                 ref = f"\n\n{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
#                 retrieved_information += text + ref
                
#             step.output = retrieved_information
            
#         return documents
    
#     async def _arun(self, query: str) -> List[Document]:
#         """
#         Get relevant documents by using the vectorstore.
        
#         :param query: The query to use to find relevant documents.
#         :type query: str
#         :param run_manager: The callback manager to use to manage callbacks.
#         :type run_manager: CallbackManagerForRetrieverRun
        
        
#         :return: List of relevant documents.
#         :rtype: List[Document]
        
#         """
#         async with cl.Step("retriever", show_input=True) as step:
#             step.input = "Query: " + query
#             documents = await self.vectordb.amax_marginal_relevance_search(query, k=3, fetch_k=10)
#             retrieved_information = "Retrieved the following documents:\n"
#             for idx, doc in enumerate(documents):
#                 text = doc.page_content
#                 ref = f"\n\n{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
#                 retrieved_information += text + ref
                
#             step.output = retrieved_information
            
#         return documents

# class RetrieverWithSearch(BaseTool):
#     """Retriever that uses a search engine to find relevant documents and then uses a retriever to get the documents from the vectorstore.

#     Args:
#         :param retriever: The retriever to use to get the documents from the vectorstore.
#         :type retriever: BaseRetriever
#         :param vectordb: The search engine to use to find relevant documents.
#         :type vectordb: VectorStore


#     """
#     vectordb: VectorStore
#     name: str = "RetrieverWithSearch"
#     description: str = "Retriever that uses a search engine to find relevant documents and then uses a retriever to get the documents from the vectorstore."
#     args_schema: Optional[Type[BaseModel]] = RetrievalInput
    
#     def _run(self, query: str) -> List[Document]:
#         """
#         Get relevant documents by using first using IndexNewArxivPapers and then retrieve.
        
#         :param query: The query to use to find relevant documents.
#         :type query: str
#         :param run_manager: The callback manager to use to manage callbacks.
#         :type run_manager: CallbackManagerForRetrieverRun
        
        
#         :return: List of relevant documents.
#         :rtype: List[Document]
        
#         """
#         with cl.Step("retriever with search", show_input=True) as step:
#             kw_llm = OpenAI()
#             kwchain = LLMChain(
#                 llm = kw_llm,
#                 prompt = PromptTemplate(
#                     template = """
#                     Given a query {query}, make another query containing keywords in a format suitable for Google Search API. 
                    
#                     For example:
#                     Query: tell me about the latest research in transformers
#                     New Query: transformers

#                     New query:\n""",
#                     input_variables = ["query"],
#                 )
#             )
#             query_keywords = kwchain.run(query)
#             #Index new papers using the tool
#             index_tool = IndexNewArxivPapers(self.vectordb)
#             index_tool._run(query_keywords)
#             step.input = "Query: " + query
#             documents = self.vectordb.max_marginal_relevance_search(query, k=3, fetch_k=10)
#             retrieved_information = "Retrieved the following documents:\n"
#             for idx, doc in enumerate(documents):
#                 text = doc.page_content
#                 ref = f"\n\n{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
#                 retrieved_information += text + ref
                
#             step.output = retrieved_information
            
#         return documents
    
#     async def _arun(self, query: str) -> List[Document]:
#         """
#         Get relevant documents by using first using IndexNewArxivPapers and then retrieve.
        
#         :param query: The query to use to find relevant documents.
#         :type query: str
#         :param run_manager: The callback manager to use to manage callbacks.
#         :type run_manager: CallbackManagerForRetrieverRun
        
        
#         :return: List of relevant documents.
#         :rtype: List[Document]
        
#         """
        
#         async with cl.Step("retriever with search", show_input=True) as step:
            
#             kw_llm = OpenAI()
#             kwchain = LLMChain(
#                 llm = kw_llm,
#                 prompt = PromptTemplate(
#                     template = """
#                     Given a query {query}, make another query containing keywords in a format suitable for Google Search API. 
                    
#                     For example:
#                     Query: tell me about the latest research in transformers
#                     New Query: transformers

#                     New query:\n""",
#                     input_variables = ["query"],
#                 )
#             )
#             query_keywords = kwchain.run(query)
#             #Index new papers using the tool
#             index_tool = IndexNewArxivPapers(self.vectordb)
#             index_tool._run(query_keywords)
            
#             step.input = "Query: " + query
#             documents = await self.vectordb.amax_marginal_relevance_search(query, k=3, fetch_k=10)
#             retrieved_information = "Retrieved the following documents:\n"
#             for idx, doc in enumerate(documents):
#                 text = doc.page_content
#                 ref = f"\n\n{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
#                 retrieved_information += text + ref
                
#             step.output = retrieved_information
            
#         return documents
def document_evaluator(documents: List[Document], query: str):
    SUMMARIZE_INSTRUCTIONS = """
        Given the following context: {documents}, summarize the key points per parent document. Based on the summary, rate the summary on a scale of 1-5, where 1 is the worst and 5 is the best,
        on whether the summary is enough to answer the following question: {query}.
        Only give me the number of the rating, no explanation.
        
        Give the answer in the following format:
        
        Summary: summary given query and context
        Rating: rating given
        """
        
    summary_chain = LLMChain(
        llm = OpenAI(
            model="gpt-3.5-turbo",
            n=4,
            best_of=4
            ),
        prompt = PromptTemplate(
            template=SUMMARIZE_INSTRUCTIONS,
            input_variables=["retrieved_context", "query"],
            )
    )
    
    summary_rating = summary_chain.run({"documents": documents, "query": query})
    
    return summary_rating
    
class Retriever(BaseTool):
    vectordb: VectorStore
    fetch_k: int = 10
    k: int = 3
    name: str = "Retriever"
    description: str  = "Retriever that find documents from the vectorstore."
    args_schema: Type[BaseModel] = RetrievalInput
    
    def _run(self, query: str) -> List[Document]:
        """
        Get relevant documents by using the vectorstore.
        
        :param query: The query to use to find relevant documents.
        :type query: str
        :param run_manager: The callback manager to use to manage callbacks.
        :type run_manager: CallbackManagerForRetrieverRun
        
        
        :return: List of relevant documents.
        :rtype: List[Document]
        
        """
        with cl.Step("RAG", show_input=True) as step:
            step.input = "Query: " + query
            
            llm = OpenAI(temperature=0.2)
            retriever = MultiQueryRetriever.from_llm(
                llm=llm, 
                retriever=self.vectordb.as_retriever(search_type="mmr", search_kwargs={"k": self.k, "fetch_k": self.fetch_k})
                )
            
            documents = retriever.get_relevant_documents(query)
            retrieved_information = "Retrieved the following documents:\n"
            for idx, doc in enumerate(documents):
                text = doc.page_content
                ref = f"\n\n{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
                retrieved_information += ref + text
                
            step.output = retrieved_information
            
        # with cl.Step("Document Evaluator", show_input=True) as step:
        #     step.input = "Query: " + query
        #     summary_rating = document_evaluator(documents, query)
        #     step.output = summary_rating
            
        return documents
    
    async def _arun(self, query: str) -> List[Document]:
        """
        Get relevant documents by using the vectorstore.
        
        :param query: The query to use to find relevant documents.
        :type query: str
        :param run_manager: The callback manager to use to manage callbacks.
        :type run_manager: CallbackManagerForRetrieverRun
        
        
        :return: List of relevant documents.
        :rtype: List[Document]
        
        """
        async with cl.Step("RAG", show_input=True) as step:
            step.input = "Query: " + query
            
            llm = OpenAI(temperature=0.2)
            retriever = MultiQueryRetriever.from_llm(
                llm=llm, 
                retriever=self.vectordb.as_retriever(search_type="mmr", search_kwargs={"k": self.k, "fetch_k": self.fetch_k})
                )
            
            documents = await retriever.aget_relevant_documents(query)
            
            elements = []
            for doc in documents:
                elements.append(cl.Text(name = doc.metadata['title'], content = doc.page_content, display = 'inline'))
                
            step.elements = elements
            step.update()
            
        return documents

class RetrieverWithSearch(BaseTool):
    """Retriever that uses a search engine to find relevant documents and then uses a retriever to get the documents from the vectorstore.

    Args:
        :param retriever: The retriever to use to get the documents from the vectorstore.
        :type retriever: BaseRetriever
        :param vectordb: The search engine to use to find relevant documents.
        :type vectordb: VectorStore


    """
    vectordb: VectorStore
    pdf_parser: Literal['PyMuPDF', 'GROBID'] = "PyMuPDF"
    search_k: int = 10
    fetch_k: int = 10
    k: int = 3
    chunk_size: int = 1024
    chunk_overlap: int = 100
    name: str = "RetrieverWithSearch"
    description: str = "Retriever that uses a search engine to find relevant documents and then uses a retriever to get the documents from the vectorstore."
    args_schema: Optional[Type[BaseModel]] = RetrievalInput
    
    def _run(self, query: str) -> List[Document]:
        """
        Get relevant documents by using first using IndexNewArxivPapers and then retrieve.
        
        :param query: The query to use to find relevant documents.
        :type query: str
        :param run_manager: The callback manager to use to manage callbacks.
        :type run_manager: CallbackManagerForRetrieverRun
        
        
        :return: List of relevant documents.
        :rtype: List[Document]
        
        """
        with cl.Step("RAG", show_input=True) as step:
            # kw_llm = OpenAI()
            # kwchain = LLMChain(
            #     llm = kw_llm,
            #     prompt = PromptTemplate(
            #         template = """
            #         Given a query {query}, make another query containing keywords in a format suitable for Google Search API. 
                    
            #         For example:
            #         Query: tell me about the latest research in transformers
            #         New Query: transformers

            #         New query:\n""",
            #         input_variables = ["query"],
            #     )
            # )
            # query_keywords = kwchain.run(query)
            #Index new papers using the tool
            index_tool = IndexNewArxivPapers(self.vectordb, 
                                             pdf_parser=self.pdf_parser,
                                             n_search_results=self.search_k)
            index_tool._run(query)
            step.input = "Query: " + query
            
            llm = OpenAI(temperature=0.2)
            retriever = MultiQueryRetriever.from_llm(
                llm=llm, 
                retriever=self.vectordb.as_retriever(search_type="mmr", search_kwargs={"k": self.k, "fetch_k": self.fetch_k})
                )
            
            documents = retriever.get_relevant_documents(query)
            retrieved_information = "Retrieved the following documents:\n"
            for idx, doc in enumerate(documents):
                text = doc.page_content
                ref = f"\n\n{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
                retrieved_information += ref + text
                
            step.output = retrieved_information
            
        return documents
    
    async def _arun(self, query: str) -> List[Document]:
        """
        Get relevant documents by using first using IndexNewArxivPapers and then retrieve.
        
        :param query: The query to use to find relevant documents.
        :type query: str
        :param run_manager: The callback manager to use to manage callbacks.
        :type run_manager: CallbackManagerForRetrieverRun
        
        
        :return: List of relevant documents.
        :rtype: List[Document]
        
        """
        
            
            # kw_llm = OpenAI()
            # kwchain = LLMChain(
            #     llm = kw_llm,
            #     prompt = PromptTemplate(
            #         template = """
            #         Given a query {query}, make another query containing keywords in a format suitable for Google Search API. 
                    
            #         For example:
            #         Query: tell me about the latest research in transformers
            #         New Query: transformers

            #         New query:\n""",
            #         input_variables = ["query"],
            #     )
            # )
            # query_keywords = kwchain.run(query)
            # #Index new papers using the tool
        async with cl.Step("arXiV search", show_input=True) as step:
            index_tool: IndexNewArxivPapers = IndexNewArxivPapers(self.vectordb, pdf_parser=self.pdf_parser, n_search_results=self.search_k)
            await index_tool._arun(query)
            step.output = f"Indexed new papers: {index_tool.ids}" 
            
        async with cl.Step("RAG", show_input=True) as step:
            step.input = "Query: " + query
            
            llm = OpenAI(temperature=0.2)
            retriever = MultiQueryRetriever.from_llm(
                llm=llm, 
                retriever=self.vectordb.as_retriever(search_type="mmr", search_kwargs={"k": self.k, "fetch_k": self.fetch_k})
                )
            
            documents = await retriever.aget_relevant_documents(query)
            retrieved_information = "Retrieved the following documents:\n"
            for idx, doc in enumerate(documents):
                text = doc.page_content + "\n\n"
                ref = f"{idx+1}. {doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}:\n"
                retrieved_information += ref + text
                
            step.output = retrieved_information
            
        return documents
    

# class DocumentEvaluatorInput(BaseModel):
#     query: str = Field(..., title="Query", description="The query used to find relevant documents with Retriever or RetrieverWithSearch.")
#     retrieved_context: str = Field(..., title="Retrieved Context", description="The context retrieved by Retriever or RetrieverWithSearch.")

# class DocumentEvaluator(BaseTool):
#     name: str = "DocumentEvaluator"
#     description: str = "Document Evaluator that summarizes the context retrieved by Retriever or RetrieverWithSearch and asks the user to rate the summary from 1 to 5."
#     args_schema: Optional[Type[BaseModel]] = DocumentEvaluatorInput
    
#     def _run(self, query: str, retrieved_context: str) -> List[Document]:
#         """Summarizes a list of documents by extracting key points per parent document retrieved.

#         Args:
#             documents (List[Document]): The list of documents to summarize.

#         Returns:
#             str: The summary of the documents.
#         """
        
#         SUMMARIZE_INSTRUCTIONS = """
#         Given the following context: {retrieved_context}, summarize the key points per parent document. Based on the summary, rate the summary on a scale of 1-5, where 1 is the worst and 5 is the best,
#         on whether the summary is enough to answer the following question: {query}.
#         Only give me the number of the rating, no explanation.
        
#         Give the answer in the following format:
        
#         Summary: summary given query and context
#         Rating: rating given
#         """
        
#         summary_chain = LLMChain(
#             llm = OpenAI(
#                 model="gpt-3.5-turbo",
#                 n=4,
#                 best_of=4
#                 ),
#             prompt = PromptTemplate(
#                 template=SUMMARIZE_INSTRUCTIONS,
#                 input_variables=["retrieved_context", "query"],
#                 )
#         )
        
#         summary_rating = summary_chain.run({"retrieved_context": retrieved_context, "query": query})
        
#         return summary_rating