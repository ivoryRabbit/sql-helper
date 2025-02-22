import textwrap
from typing import Optional, Dict
from dataclasses import dataclass

from sqlalchemy import select
from temporalio import activity

from client import openai_async
from client.database import embedding_model, session_maker
from model.ddl_collection import DDLCollection


@dataclass
class TextToSQLParams:
    dialect: str
    question: str


def generate_system_message(message: str) -> Dict[str, str]:
    return {"role": "system", "content": message}


def generate_user_message(message: str) -> Dict[str, str]:
    return {"role": "user", "content": message}


def generate_assistant_message(message: str) -> Dict[str, str]:
    return {"role": "assistant", "content": message}


initial_prompt = textwrap.dedent(
    """
    당신은 {dialect} 전문가입니다. 유저의 질문에 대해 SQL 쿼리를 생성하여 답변해주세요.
    제공되는 컨텍스트를 참고하여 SQL 쿼리를 생성해야 하며, 반드시 가이드라인을 준수하여 응답해주세요.
    """
)

guideline_prompt = textwrap.dedent(
    """
    ==Response Guidelines
    1. 제공된 컨텍스트가 충분하다면 질문에 대한 설명 없이 정확한 SQL 쿼리를 생성해주세요.
    2. 제공된 컨텍스트가 충분하지 않을 때에는 쿼리를 생성할 수 없는 이유를 설명해주세요.
    3. 컨텍스트에서 테이블 리스트가 주어지면 그 중에서 가장 관련성 높은 테이블들을 사용해주세요.
    4. JOIN 구문을 사용할 경우, 반드시 테이블 별칭(alias)을 명시해 주세요. 
    5. Subquery의 depth가 2보다 큰 경우, CTE를 사용해주세요.
    6. 응답 전에 쿼리의 문법이 맞는지, 사용한 컬럼이 테이블에 존재하는지 한번 더 확인해주세요.
    7. SQL 쿼리를 응답해야 하는 경우에는 SQL 포멧으로 정리해서 응답해주세요.
    """
)


@activity.defn
async def submit_prompts(params: TextToSQLParams) -> Optional[str]:
    client = openai_async.get_client()

    model = "gpt-3.5-turbo"
    temperature = 0.2
    max_tokens = 4096

    question_vector = embedding_model.encode(params.question)

    with session_maker.begin() as session:
        rows = session.scalars(
            select(DDLCollection)
            .order_by(
                DDLCollection
                .embedding
                .cosine_distance(question_vector)
            )
            .limit(2)
        ).all()

    context_prompt = "\n".join([row.ddl_content for row in rows])

    prompts = [
        generate_system_message(initial_prompt.format(dialect=params.dialect) + context_prompt + guideline_prompt),
        generate_user_message(params.question)
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=prompts,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    results = response.choices[0].message.content
    return results
