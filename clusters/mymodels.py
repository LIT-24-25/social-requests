import json
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from clusters.instances import openrouter_token, gigachat_token
from openai import OpenAI
from pydantic import BaseModel
import instructor

class OutputFormat(BaseModel):
    summary: str

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

    data = completion.summary
    return data

def call_gigachat(prompt):
    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.USER,
                content=prompt
            )
        ],
        temperature=0,
    )
    with GigaChat(credentials=gigachat_token, verify_ssl_certs=False) as giga:
        response = giga.chat(payload)
        return response.choices[0].message.content