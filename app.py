from arxiv_bot.functions import (
    clear_pdf,
    init_file_upload,
    process_pdf_upload,
    load_bot,
    load_memory,
    load_vectordb,
    init_chat_settings
)
from arxiv_bot.search import ProcessPDF
from dotenv import load_dotenv
import chainlit as cl
import os
import warnings
warnings.filterwarnings("ignore")

try:
    load_dotenv(override=True)
except:
    pass

@cl.on_settings_update
async def on_settings_update(settings: dict):
    vectordb = cl.user_session.get('vectordb')
    cl.user_session.set('settings', settings)
    cl.user_session.set('pdf_processor', ProcessPDF(
        vectordb, 
        settings['pdf_parser'],
        int(settings['chunk_size']),
        int(settings['chunk_overlap'])))
    
    load_bot()
    

@cl.on_chat_start
async def start():
    COLLECTION_NAME = "arxiv"
    PERSIST_DIR = "arxiv_vdb"
    
    clear_pdf()
    os.makedirs("./pdfs", exist_ok=True)
    os.makedirs("./output", exist_ok=True)
    await init_chat_settings()
    load_memory()
    load_vectordb(
        collection_name=COLLECTION_NAME,
        persist_dir=PERSIST_DIR,
    )
    load_bot()
    
    # ## Ask user if they want to upload a file.
    # init_msg = cl.AskActionMessage(
    #     content = "Welcome to arXiv AI Research Assistant! Would you like to upload some papers?",
    #     actions = [
    #         cl.Action(name = 'Yes', value = 'Yes', label='✅ Yes'),
    #         cl.Action(name = 'No', value = 'No', label = '❌ No')
    #     ]
    # )
    
    # upload_bool = await init_msg.send()
    
    
    # if upload_bool and upload_bool.get("value") == 'Yes':
        
    #     files = None
    #     ask_file_message = cl.AskFileMessage(
    #         content = "Please upload the papers here.",
    #         accept = [".pdf"],
    #         max_size_mb = 10,
    #         max_files = 10
    #     )
    #     files = await ask_file_message.send()
        
    #     if files:
    #         await init_file_upload(ask_file_message, files)
    
    # else:
    #     init_msg.content = "No worries! Ask me anything regarding a specific topic found on arXiv papers and I'll try my best to answer!"
    #     init_msg.actions = []
    #     await init_msg.update()

        
@cl.on_message
async def main(query: cl.Message):
    bot = cl.user_session.get('bot')
    
    if query.elements:    
        await process_pdf_upload([file for file in query.elements if file.mime == 'application/pdf'])
    
    response = await bot.acall({"input": query.content}) #type: ignore
    answer = cl.Message(content=response['output'])
    intermediate_steps = response['intermediate_steps']
    
    # Get sources
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
                    
    answer.elements = sources #type: ignore
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