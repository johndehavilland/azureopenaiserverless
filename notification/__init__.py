import datetime
import random
import json
import logging
import openai
import os
import time
from azure.messaging.webpubsubservice import WebPubSubServiceClient

import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    pubsubconnstring = os.getenv("AZURE_PUBSUB_CONNECTION_STRING")
    service = WebPubSubServiceClient.from_connection_string(connection_string=pubsubconnstring, hub='Hub', logging_enable=False)
    
    req_body = req.get_json()
    my_input = req_body.get('question')
    logging.info('Python HTTP trigger function processed a request. Input: %s', my_input)


    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT") # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
    openai.api_type = 'azure'
    openai.api_version = '2023-07-01-preview' # this may change in the future

    deployment_name='gpt35' #This will correspond to the custom name you chose for your deployment when you deployed a model. 

    # Send a completion call to generate an answer
    logging.info('Sending a completion job')

    response = openai.ChatCompletion.create(
        engine="gpt35",
        messages = [{"role":"system","content":"You are an AI assistant that helps people find information."},{"role":"user","content":"who is jfk?"},{"role":"assistant","content":"JFK is an acronym that refers to John Fitzgerald Kennedy, who was the 35th President of the United States. He served as President from 1961 until his assassination in 1963. Kennedy was known for his charisma, his advocacy for civil rights, and his handling of the Cold War. His presidency is also associated with the Bay of Pigs invasion, the Cuban Missile Crisis, and the Apollo space program."}],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
    
    # response = openai.Completion.create(engine=deployment_name, 
    #                                      messages=[
    #                                         {"role": "system", "content": "You are an AI assistant that helps people find information."},
    #                                         {"role": "user", "content": my_input}
    #                                     ], 
    #                                     max_tokens=100,
    #                                     temperature=0.7,
    #                                     top_p=0.95,
    #                                     frequency_penalty=0,
    #                                     presence_penalty=0,
    #                                     stream=True)
    final = False
    first=True

    while final == False:
        for chunk in response:
            logging.info('Chunk received')
            content = chunk['choices'][0]['message']['content'].replace('\n', ' ').replace('\r', '').replace('\t', ' ').replace('\b', ' ').replace('\f', ' ')
            finish_reason = chunk['choices'][0]['finish_reason']
            if content is not None:
                logging.info(content)
                logging.info(finish_reason)
                timecheck = datetime.datetime.now().strftime("%A %d-%b-%Y %H:%M:%S")
                service.send_to_all(message = {
                    'msgchunk': content,
                    'first':first,
                    'end':False
                },logging_enable=False)
                first=False
            if finish_reason is not None:
                logging.info("finish_reason not null")
                final = True
    
    service.send_to_all(message = {
                    'msgchunk': "",
                    'first':False,
                    'end':True
                },logging_enable=False)
    
    return func.HttpResponse("ok", status_code=200)
