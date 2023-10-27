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
        engine="gpt35-turbo-latest",
        messages = [{"role":"system","content":"You are an AI assistant that helps people find information."},
                    {"role":"user","content":my_input}],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=True)
    
    final = False
    first=True

    while final == False:
        for chunk in response:
            logging.info('Chunk received')
            logging.info(chunk)
            try:
                chunk_message = chunk['choices'][0]['delta']
                finish_reason = chunk['choices'][0]['finish_reason']
                if chunk_message is not None:
                    logging.info(chunk_message)
                    logging.info(finish_reason)
                    timecheck = datetime.datetime.now().strftime("%A %d-%b-%Y %H:%M:%S")
                    service.send_to_all(message = {
                        'msgchunk': chunk_message,
                        'first':first,
                        'end':False
                    },logging_enable=False)
                    first=False
                if finish_reason is not None:
                    logging.info("finish_reason not null")
                    final = True
            except:
                logging.info("error")
    
    service.send_to_all(message = {
                    'msgchunk': "",
                    'first':False,
                    'end':True
                },logging_enable=False)
    
    return func.HttpResponse("ok", status_code=200)
