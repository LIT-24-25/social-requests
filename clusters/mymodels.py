import requests
import json
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from clusters.instances import openrouter_token, gigachat_token

def call_qwen(prompt):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openrouter_token}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "qwen/qwen-plus",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],

        }, indent=2)
    )

    data = response.json()
    return data['choices'][0]['message']['content']

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
    