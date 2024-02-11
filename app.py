from dotenv import load_dotenv
import chainlit as cl
from chainlit.input_widget import Slider, Select, TextInput
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai import OpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent
from langchain.vectorstores import chroma, VectorStore
from langchain_core.documents import Document
from langchain.agents.agent import AgentExecutor
from langchain.chains import LLMChain
from langchain_core.tools import BaseTool
from arxiv_bot.retrievers import Retriever, RetrieverWithSearch
from typing import List
import os
import chromadb
from arxiv_bot.prompts import PREFIX, SUFFIX, FORMAT_INSTRUCTIONS
import shutil

try:
    load_dotenv()
except:
    pass

def load_llm(settings: dict) -> ChatOpenAI:
    
    return ChatOpenAI(
        model = 'gpt-3.5-turbo-1106',
        streaming = True,
        temperature = settings['temperature'],
    )
    
def summarize(query: str, documents: List[Document]) -> str:
    """Summarizes a list of documents by extracting key points per parent document retrieved.

    Args:
        documents (List[Document]): The list of documents to summarize.

    Returns:
        str: The summary of the documents.
    """
    chunks = "\n\n".join([chunk.page_content + f"\nReference : {chunk.metadata['title']}, {chunk.metadata['paper_id']}" for chunk in documents])
    SUMMARIZE_INSTRUCTIONS = """Given the following documents: {chunks}, summarize the key points per parent document. 
    Summary:
    """
    
    summary_chain = LLMChain(
        llm = OpenAI(
            model="gpt-3.5-turbo",
            n=4,
            best_of=4
            ),
        prompt = PromptTemplate(
            template=SUMMARIZE_INSTRUCTIONS,
            input_variables=["chunks"],
            )
    )
    
    summary = summary_chain.run({"chunks": chunks})
    
    return summary
    
def load_tools(vectordb: VectorStore, settings: dict) -> List[BaseTool]:
    
    # HYDE_PROMPT_TEMPLATE = """
    # Please answer the user's questions regarding specific topics in the latest research papers in Arxiv.
    # Questions: {question}
    # Answer:
    # """
    # hyde_prompt = PromptTemplate(
    #     template=HYDE_PROMPT_TEMPLATE,
    #     input_variables=["question"],
    #     )
    
    # hyde_chain = LLMChain(
    #     llm = OpenAI(
    #         model="gpt-3.5-turbo-instruct",
    #         n=4,
    #         best_of=4
    #         ),
    #     prompt = hyde_prompt
    # )
    
    # embeddings = HypotheticalDocumentEmbedder(
    #     llm_chain = hyde_chain,
    #     base_embeddings = base_embeddings,
    # )
    

    retriever = Retriever(
                    vectordb=vectordb,
                    fetch_k = settings['fetch_k'],
                    k = settings['k'],
                    )
    
    retriever_with_search = RetrieverWithSearch(
                                    vectordb=vectordb,
                                    pdf_parser=settings['pdf_parser'],
                                    search_k=settings['search_k'],
                                    fetch_k=settings['fetch_k'],
                                    k=settings['k'],
                                    chunk_size=settings['chunk_size'],
                                    chunk_overlap=settings['chunk_overlap'],
    )
    
    return [retriever, retriever_with_search]
    
    
def load_bot(vectordb: VectorStore, settings: dict) -> AgentExecutor:
    """
    Loads the bot with the tools and the language model
    
    :return: the bot
    :rtype: Agent
    """
    
    tools: List[BaseTool] = load_tools(vectordb, settings)
    llm = load_llm(settings)

    memory = cl.user_session.get('memory')

    agent: AgentExecutor = initialize_agent(
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
        
    
    return agent

@cl.on_settings_update
async def on_settings_update(settings: dict):
    vectordb: VectorStore = cl.user_session.get('vectordb') #type: ignore
    bot = load_bot(vectordb, settings)
    cl.user_session.set('bot', bot)

@cl.on_chat_start
async def start():
    # msg = cl.Message(content="Initializing bot...")
    # await msg.send()
    # msg.content = "Hi there! I am a bot that is very knowledgable in the latest research papers in Arxiv. Ask me anything!"
    # await msg.update()
    
    try:
        shutil.rmtree("./pdfs")
        shutil.rmtree("./output")
        chromadb.PersistentClient(path="arxiv_vdb").delete_collection("arxiv")
    except:
        pass
    
    settings = await cl.ChatSettings(
        [
            TextInput(id="search_k", label="# of web search results", initial="5"),
            TextInput(id="fetch_k", label="# of initial papers to fetch", initial="10"),
            TextInput(id="k", label="# of papers for context", initial="3"),
            TextInput(id="chunk_size", label="Chunk size", initial="1024"),
            TextInput(id="chunk_overlap", label="Chunk overlap", initial="100"),
            Slider(id="temperature", label="Temperature", min=0.0, max=1.0, step=0.1, initial=0.0),
            Select(id = "pdf_parser", label = "Parser", values = ["PyMuPDF", "GROBID"], initial_index=0),
            
        ]
    ).send()
    
    memory = ConversationBufferWindowMemory(memory_key='chat_history', 
                                        input_key='input',
                                        output_key='output',
                                        return_messages=True,
                                        k=5,
                                        )
    cl.user_session.set('memory', memory)
    
    COLLECTION_NAME = "arxiv"
    PERSIST_DIR = "arxiv_vdb"
    
    os.makedirs(PERSIST_DIR, exist_ok=True)
    
    base_embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    vectordb = chroma.Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
        embedding_function=base_embeddings)
    cl.user_session.set('vectordb', vectordb)
    
    bot = load_bot(vectordb, settings)
    cl.user_session.set('bot', bot)


@cl.on_message
async def main(query):
    # FINAL_ANSWER_PREFIX = '{\n    "action": "Final Answer",\n    "action_input": "'
    bot = cl.user_session.get('bot')
        
    response = await bot.acall(query.content) #type: ignore
    answer = cl.Message(content=response['output'])
    intermediate_steps = response['intermediate_steps']
    
    sources = []
    if len(intermediate_steps) > 0:
        for step in intermediate_steps:
            action = step[0]
            output = step[1]
            
            if action.tool == 'Retriever' or action.tool == 'RetrieverWithSearch':
                refs_list = {}
                for doc in output:
                    title = doc.metadata['title']
                    paper_id = doc.metadata['paper_id']
                    link = f"https://arxiv.org/pdf/{paper_id}"
                    
                    if paper_id not in refs_list:
                        refs_list[paper_id] = {'title': title, 'link': link}

                for id, metadata in refs_list.items():
                    sources.append(
                        cl.Text(name = metadata['title'], content = f"arXiv ID: {id}\nLink: {metadata['link']}", display='inline')
                    )    
                    
    answer.elements = sources
    await answer.send()
# @cl.on_message
# async def main(query):
#     FINAL_ANSWER_PREFIX = '{\n    "action": "Final Answer",\n    "action_input": "'
#     bot = cl.user_session.get('bot')
#     answer = cl.Message(content="")
#     answer_temp = ""
#     refs = ""
        
#     stream = bot.astream_log({"input": query.content}, include_names=['ChatOpenAI']) #type: ignore     
#     async for chunk in stream:
#         val = chunk.ops[0]
#         # print(val['value'])
#         if 'intermediate_steps' in val['value']:
#             intermediate_steps = val['value']['intermediate_steps']
#             if len(intermediate_steps) > 0 and isinstance(intermediate_steps, list):
#                 for step in intermediate_steps:
#                     action = step[0]
#                     output = step[1]
#                     print(action, output)
                    
#                     if action.tool == 'retriever' or action.tool == 'retriever_with_search':
#                         refs_list = []
#                         for doc in output:
#                             refs_list.append(f"\n{doc.metadata['title']}, arXiv ID: {doc.metadata['paper_id']}\n")
                            
#                         refs += ''.join(set(refs_list))                        
#                         if refs != '':                        
#                             refs = f"\n\nReferences: {refs}"
                        
#         elif isinstance(val['value'], str):
#             if FINAL_ANSWER_PREFIX in answer_temp:
#                 new_val = val['value'].replace('"', '').replace('}', '')
#                 await answer.stream_token(new_val)
#                 print(answer.content)
#             else:
#                 answer_temp += val['value']
#         else:
#             continue
#     answer.content += refs
#     await answer.send()


@cl.on_chat_end
def on_chat_end():
    pass