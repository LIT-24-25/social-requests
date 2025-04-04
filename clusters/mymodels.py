from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from clusters.instances import openrouter_token, gigachat_token
from openai import OpenAI
from pydantic import BaseModel, Field
import instructor

class OutputFormat(BaseModel):
    name: str = Field(description="Name of the cluster, that describes the main problem, containing 2-3 words", default='Не удалось сгенерировать название')
    summary: str = Field(description="Summary of the complaints, containing 10-20 words", default='Не удалось сгенерировать описание')

def call_qwen(prompt):
    try:
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
            response_model=OutputFormat,
            temperature=0,
            max_tokens=1024,
            timeout=60,
            max_retries=3
        )
        
        # Ensure we have valid name and summary
        name = completion.name if completion.name else 'Unnamed Cluster'
        summary = completion.summary if completion.summary else 'No summary available'
        
        return name, summary
    except Exception as e:
        print(f"Error in call_qwen: {str(e)}")
        return "Error", "Failed to generate summary"

def call_gigachat(prompt):
    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.USER,
                content=prompt
            )
        ],
        temperature=0
    )
    with GigaChat(credentials=gigachat_token, verify_ssl_certs=False) as giga:
        response = giga.chat(payload)
    result = response.choices[0].message.content
    return result     
