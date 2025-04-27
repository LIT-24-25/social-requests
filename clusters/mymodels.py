from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from instructor.exceptions import InstructorRetryException

from clusters.instances import openrouter_token, gigachat_token
from openai import OpenAI
from pydantic import BaseModel, Field
import instructor

class OutputFormat(BaseModel):
    name: str = Field(description="Name of the cluster, that describes the main problem, containing 2-3 words", default='Не удалось сгенерировать название')
    summary: str = Field(description="Summary of the complaints, containing 10-20 words", default='Не удалось сгенерировать описание')

def call_openrouter(prompt):
    try:
        client = instructor.from_openai(OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_token,
        ), mode=instructor.Mode.TOOLS)
        completion = client.chat.completions.create(
            model = "qwen/qwen-plus",
            extra_body={"models": ["deepseek/deepseek-chat-v3-0324", "qwen/qwen-max"], "provider": {"require_parameters": True}},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_model=OutputFormat,
            temperature=0,
            max_retries=3,
            max_tokens=500
        )
        # Ensure we have valid name and summary
        name = completion.name if completion.name else 'Unnamed Cluster'
        summary = completion.summary if completion.summary else 'No summary available'
        model_name = completion._raw_response.model
    
        return name, summary, model_name
    except InstructorRetryException as e:
        print(e.last_completion)

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
