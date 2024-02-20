from arxiv_bot.prompts import PREFIX, SUFFIX, FORMAT_INSTRUCTIONS
from arxiv_bot.retrievers import Retriever, RetrieverWithSearch
from arxiv_bot.search import ProcessPDF
from chainlit.input_widget import Slider, Select, TextInput
from chainlit.message import AskFileMessage
from chainlit.types import AskFileResponse
from chainlit.element import ElementBased
from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.vectorstores import chroma, VectorStore
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from typing import List, Any
import chainlit as cl
import chromadb
import os
import shutil


def clear_pdf():
    """
    Remove all pdf files from pdfs directory and output directory. Also, remove all documents from arxiv collection in the database.
    """
    try:
        shutil.rmtree("./pdfs")
        shutil.rmtree("./output")
        chromadb.PersistentClient(path="arxiv_vdb").delete_collection("arxiv")
    except:
        pass
    
def load_llm() -> ChatOpenAI:
    
    settings = cl.user_session.get('settings')
    return ChatOpenAI(
        model = settings['llm_model'],
        streaming = True,
        temperature = float(settings['temperature']),
    )
    
def load_tools() -> List[BaseTool]:
    
    settings = cl.user_session.get('settings')
    vectordb = cl.user_session.get('vectordb')
    
    retriever = Retriever(
                    vectordb=vectordb,
                    fetch_k = int(settings['fetch_k']),
                    k = int(settings['k']),
                    )
    
    retriever_with_search = RetrieverWithSearch(
                                    vectordb=vectordb,
                                    pdf_parser=settings['pdf_parser'],
                                    search_k=int(settings['search_k']),
                                    fetch_k=int(settings['fetch_k']),
                                    k=int(settings['k']),
                                    chunk_size=int(settings['chunk_size']),
                                    chunk_overlap=int(settings['chunk_overlap']),
    )
    
    return [retriever, retriever_with_search]

async def init_chat_settings():
    settings = await cl.ChatSettings(
        [
            Select(
                id='llm_model',
                label='Language Model',
                values=[
                    "gpt-4-0125-preview",
                    "gpt-4-turbo-preview",
                    "gpt-4-1106-preview",
                    "gpt-4",
                    "gpt-4-0613",
                    "gpt-4-32k",
                    "gpt-4-32k-0613",
                    "gpt-3.5-turbo-0125",
                    "gpt-3.5-turbo",
                    "gpt-3.5-turbo-1106",
                    "gpt-3.5-turbo-instruct",
                    "gpt-3.5-turbo-16k",
                    "gpt-3.5-turbo-0613",
                    "gpt-3.5-turbo-16k-0613"
                ], 
                initial_value = os.environ.get("INIT_LLM"),
                tooltip="The language model to use for the conversation. For more information, see https://platform.openai.com/docs/models/overview."
            ),
            Slider(id="temperature", label="Temperature", min=0.0, max=1.0, step=0.1, initial=0.0),
            Select(
                id='embedding_model',
                label='Embedding Model',
                values=[
                    "text-embedding-3-large",
                    "text-embedding-3-small",
                    "text-embedding-ada-002"
                ],
                initial_value = os.environ.get("INIT_EMBEDDING"),
                tooltip="The embedding model to use for the vector database. For more information, see https://platform.openai.com/docs/models/overview."
            ),
            Slider(
                id="chat_history",
                label="Chat History",
                min=1,
                max=10,
                step=1,
                initial=5,
                tooltip="The number of previous messages to consider for context."
            ),
            TextInput(id="search_k", label="# of web search results", initial="5"),
            Select(
                id = "pdf_parser",
                label = "Parser",
                values = ["PyMuPDF", "GROBID"],
                initial_index=0,
                tooltip="The parser to use for extracting text from PDFs. PyMuPDF: Faster, but less accurate. GROBID: Slower, but more accurate."
            ),
            TextInput(id="fetch_k", label="# of initial papers to fetch", initial="10"),
            TextInput(id="k", label="# of papers for context", initial="3"),
            TextInput(id="chunk_size", label="Chunk size", initial="1024"),
            TextInput(id="chunk_overlap", label="Chunk overlap", initial="100"),
            
        ]
    ).send()
    cl.user_session.set('settings', settings)

def load_memory():
    memory = ConversationBufferWindowMemory(memory_key='chat_history', 
                                    input_key='input',
                                    output_key='output',
                                    return_messages=True,
                                    k=cl.user_session.get('settings')['chat_history'],
                                    )
    cl.user_session.set('memory', memory)

def load_vectordb(
    persist_dir: str,
    collection_name: str,
    ):
    os.makedirs(persist_dir, exist_ok=True)
    
    embedding_model = cl.user_session.get('settings')['embedding_model']
    base_embeddings = OpenAIEmbeddings(model=embedding_model)
    
    # _ = chromadb.PersistentClient(persist_dir).create_collection(collection_name)
    
    vectordb = chroma.Chroma(
        collection_name=collection_name,
        persist_directory=persist_dir,
        embedding_function=base_embeddings)
    cl.user_session.set('vectordb', vectordb)


def load_bot():
    """
    Loads the bot with the tools and the language model
    
    :param vectordb: the vector database
    :type vectordb: VectorStore
    :param settings: chat settings
    :type settings: dict[str, Any]
    
    :return: the bot
    :rtype: Agent
    """
    
    tools = load_tools()
    llm = load_llm()
    memory = cl.user_session.get('memory')
    agent = initialize_agent(
        tools,
        llm,
        verbose=True,
        agent = "chat-conversational-react-description",
        agent_kwargs = {
            'system_message': PREFIX,
            'human_message': SUFFIX,
            'format_instructions': FORMAT_INSTRUCTIONS,
            },
        memory = memory,
        handle_parsing_errors=True,
        return_intermediate_steps=True
        )
        
    cl.user_session.set('bot', agent)
    # return agent

async def init_file_upload(
    ask_file_message: AskFileMessage,
    files: List[AskFileResponse],
    ):
    
    settings = cl.user_session.get('settings')
    vectordb = cl.user_session.get('vectordb')
    
    async with cl.Step(name = "PDF Processor", show_input=True) as step:
        
        step.elements = [cl.Text(name = "PDFs:", content = "\n".join(["- " + file.name for file in files]), display='inline')]
        await step.update()
        
        cl.user_session.set('pdf_processor', ProcessPDF(
            vectordb, 
            settings['pdf_parser'],
            int(settings['chunk_size']),
            int(settings['chunk_overlap']))
        )
    
        os.makedirs("./pdfs", exist_ok=True)
        for file in files:
            os.rename(file.path, f"./pdfs/{file.name}")
            file.path = f"./pdfs/{file.name}"

        process_pdf = cl.user_session.get('pdf_processor')            
        await cl.make_async(process_pdf.process)([file.path for file in files])
            
        ask_file_message.content = "Finished processing PDFs. Ask me anything!"
        await ask_file_message.update()   
    
    
async def process_pdf_upload(files: List[ElementBased]):
    if not all([file.mime == 'application/pdf' for file in files]):
        raise ValueError("All files have to be PDFs.")
    
    settings = cl.user_session.get('settings')
    vectordb = cl.user_session.get('vectordb')
    
    async with cl.Step(name = "PDF Processor", show_input=True) as step:
        
        step.elements = [cl.Text(name = "PDFs:", content = "\n".join(["- " + file.name for file in files]), display='inline')]
        await step.update()
        
        cl.user_session.set('pdf_processor', ProcessPDF(
            vectordb, 
            settings['pdf_parser'],
            int(settings['chunk_size']),
            int(settings['chunk_overlap']))
        )
        print(settings['pdf_parser'])
    
        for file in files:
            os.rename(str(file.path), f"./pdfs/{file.name}")
            file.path = f"./pdfs/{file.name}"

        process_pdf = cl.user_session.get('pdf_processor')            
        await cl.make_async(process_pdf.process)([file.path for file in files])
            
        
    
# def summarize(query: str, documents: List[Document]) -> str:
#     """Summarizes a list of documents by extracting key points per parent document retrieved.

#     Args:
#         documents (List[Document]): The list of documents to summarize.

#     Returns:
#         str: The summary of the documents.
#     """
#     chunks = "\n\n".join([chunk.page_content + f"\nReference : {chunk.metadata['title']}, {chunk.metadata['paper_id']}" for chunk in documents])
#     SUMMARIZE_INSTRUCTIONS = """Given the following documents: {chunks}, summarize the key points per parent document. 
#     Summary:
#     """
    
#     summary_chain = LLMChain(
#         llm = OpenAI(
#             model="gpt-3.5-turbo",
#             n=4,
#             best_of=4
#             ),
#         prompt = PromptTemplate(
#             template=SUMMARIZE_INSTRUCTIONS,
#             input_variables=["chunks"],
#             )
#     )
    
#     summary = summary_chain.run({"chunks": chunks})
    
#     return summary