import json
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from clusters.instances import openrouter_token, gigachat_token
from openai import OpenAI
from pydantic import BaseModel, Field
import instructor
from clusters.token_manager import token_manager

class OutputFormat(BaseModel):
    name: str = Field(description="Name of the cluster, that describes the main problem, containing 2-3 words", default='Не удалось сгенерировать название')
    summary: str = Field(description="Summary of the complaints, containing 10-20 words", default='Не удалось сгенерировать описание')

def call_qwen(prompt):
    client = instructor.from_openai(OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_token,
    ))

    completion = client.chat.completions.create(
        model="qwen/qwen-plus",
        messages=[
            {
            "role": "user",
            "content": prompt
            }
        ],
        response_model=OutputFormat
    )

    name = completion.name
    summary = completion.summary
    return name, summary

def call_gigachat(prompt):
    token = token_manager.get_token()
    client = instructor.from_openai(OpenAI(
        base_url="https://gigachat.devices.sberbank.ru/api/v1",
        api_key=token,
    ))
    try:
        completion = client.chat.completions.create(
            model="GigaChat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_model=OutputFormat 
        )
        name = completion.name
        summary = completion.summary
        return name, summary     
    except Exception as e:
        print(e)
        return call_qwen(prompt)
