from dotenv import load_dotenv
import chainlit as cl
from chainlit.input_widget import Slider, Switch, Select, TextInput
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai import OpenAI
from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import create_openai_functions_agent, initialize_agent
from langchain.tools.retriever import create_retriever_tool
from langchain.agents.agent_types import AgentType
from arxiv_bot.search import IndexNewArxivPapers
from langchain.vectorstores import chroma, VectorStore
from langchain_core.documents import Document
from langchain_core.callbacks.manager import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain.agents.agent import AgentExecutor
from langchain.schema.retriever import BaseRetriever
from langchain.chains import HypotheticalDocumentEmbedder, LLMChain
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.tools import Tool, BaseTool
from arxiv_bot.retrievers import Retriever, RetrieverWithSearch
from typing import List, Tuple
import os
import glob
import chromadb
from langchain.retrievers.multi_query import MultiQueryRetriever
import shutil

load_dotenv()

def load_llm(settings: dict) -> ChatOpenAI:
    
    temp = float(settings['temp'])
    
    return ChatOpenAI(
        model = 'gpt-3.5-turbo-1106',
        temperature = temp,
        streaming = True
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
    
def load_tools(settings: dict) -> List[BaseTool]:
    base_embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    
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

    COLLECTION_NAME = "arxiv"
    PERSIST_DIR = "arxiv_vdb"
    
    os.makedirs(PERSIST_DIR, exist_ok=True)
    
    search_k = int(settings['search_k'])
    fetch_k = int(settings['fetch_k'])
    k = int(settings['k'])

    vectordb = chroma.Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
        embedding_function=base_embeddings)

    retriever = Retriever(vectordb=vectordb, 
                          search_k=search_k,
                          fetch_k=fetch_k,
                          k=k
                          )
    retriever_with_search = RetrieverWithSearch(
        vectordb=vectordb,
        search_k=search_k,
        fetch_k=fetch_k,
        k=k,
    )
    
    return [retriever, retriever_with_search]
    
    
def load_bot(settings: dict) -> AgentExecutor:
    """
    Loads the bot with the tools and the language model
    
    :return: the bot
    :rtype: Agent
    """
    tools: List[BaseTool] = load_tools(settings)
    llm = load_llm(settings)
    
    
    PREFIX = """
    You are an assistant that is very knowledgable in the latest research papers in ArXiv and 
    you provide detailed and in depth answers to questions regarding a specific topic. The assistant is aware
    of its own knowledge and will determine if it has enough information to answer the question.
    If it does not, it will ask the user to use a tool to retrieve more information.
    After using the tool, it should assess if it has enough information to answer the question.
    If not, then it will try another tool.
    """
    FORMAT_INSTRUCTIONS = """RESPONSE FORMAT INSTRUCTIONS
        ----------------------------

        When responding to me, please output a response in one of two $JSON_BLOB formats:

        **Option 1:**
        Use this if you want the human to use a tool.
        Markdown code snippet formatted in the following schema:

        ```json
        {{{{
            "action": string, \\\\ The action to take. Must be one of {tool_names}
            "action_input": string \\\\ The input to the action
        }}}}
        ```

        **Option #2:**
        Use this if you want to respond directly to the human. Markdown code snippet formatted in the following schema:

        ```json
        {{{{
            "action": "Final Answer",
            "action_input": string \\\\ You should put what you want to return to use here
        }}}}
        
        """
        
    SUFFIX = """TOOLS
        ------
        Assistant can ask the user to use tools to look up information that may be helpful in answering the users original question. The tools the human can use are:

        {{tools}}

        Answer general knowledge questions or handle conversations without a tool.
        If a specific knowledge is need regarding a certain topic, the assistant will ask the user to use the 'Retriever'. TRY THIS TOOL FIRST AND SEE IF THE RETRIEVER CAN ANSWER THE QUESTION.
        If no relevant documetns are retrieved, then it will look for more information online with the 'RetrieverWithSearch' tool. TRY THIS SECOND.
        Then, summarize the information retrieved and answer the question in great detail.
        
        {format_instructions}
        
        ALWAYS use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action:
        ```
        $JSON_BLOB
        ```
        Observation: the result of the action
        ... (this Thought/Action/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        USER'S INPUT
        --------------------
        Here is the user's input and chat history (remember to respond with the above format):
        
        Previous conversation history:
        {{{{chat_history}}}}
        
        Input:
        {{{{input}}}}
        
        Begin!
        
        """

        # TEMPLATE_TOOL_RESPONSE = """TOOL RESPONSE: 
        # ---------------------
        # {observation}

        # USER'S INPUT
        # --------------------

        # Okay, so what is the response to my last comment? If using information obtained from the tools you must mention it explicitly without mentioning the tool names - I have forgotten all TOOL RESPONSES! Remember to respond with a markdown code snippet of a $JSON_BLOB with a single action, and NOTHING else."""

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
    bot = load_bot(settings)
    cl.user_session.set('bot', bot)

@cl.on_chat_start
async def start():
    # msg = cl.Message(content="Initializing bot...")
    # await msg.send()
    # msg.content = "Hi there! I am a bot that is very knowledgable in the latest research papers in Arxiv. Ask me anything!"
    # await msg.update()
    settings = await cl.ChatSettings(
        [
            TextInput(id="search_k", label="# of web search results", initial="5"),
            TextInput(id="fetch_k", label="# of initial papers to fetch", initial="10"),
            TextInput(id="k", label="# of papers for context", initial="3"),
            Slider(id="temp", label="Temperature", min=0.0, max=1.0, step=0.1, initial=0.0),
            Select(id = "parser", label = "Parser", values = ["PyMuPDF", "GROBID"], initial_index=1),
            
        ]
    ).send()
    
    memory = ConversationBufferWindowMemory(memory_key='chat_history', 
                                        input_key='input',
                                        output_key='output',
                                        return_messages=True,
                                        k=5,
                                        )
    cl.user_session.set('memory', memory)
    print(memory, cl.user_session.get('memory'))
    
    bot = load_bot(settings)
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
    # try:
    #     shutil.rmtree("./pdfs")
    #     shutil.rmtree("./output")
    #     chromadb.PersistentClient(path="arxiv_vdb").delete_collection("arxiv")
    # except:
    #     pass
    pass