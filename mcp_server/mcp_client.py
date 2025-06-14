import os
import asyncio
import textwrap

from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio


async def run(mcp_server: MCPServer):
    instructions = textwrap.dedent(
        f"""
        당신은 Trino SQL 전문가입니다. 유저의 질문에 대해 SQL 쿼리를 생성하고 MCP 도구를 이용해 답변해주세요.
        MCP 도구를 사용하기 전에 제공되는 컨텍스트를 참고하여 SQL 쿼리를 생성해야 하며, 반드시 가이드라인을 준수하여 SQL 쿼리를 작성해주세요..
        
        ==Given Context
        CREATE TABLE movielens.users (
            id INTEGER,
            gender VARCHAR COMMENT 'The value should be either female "F" or male "M"',
            age INTEGER,
            occupation VARCHAR,
            zip_code VARCHAR
        )
        
        CREATE TABLE movielens.ratings (
            user_id INTEGER,
            movie_id INTEGER,
            rating INTEGER,
            timestamp BIGINT
        )
        
        CREATE TABLE movielens.movies (
            id INTEGER,
            title VARCHAR,
            genres VARCHAR
        )

        ==Response Guidelines
        1. 제공된 컨텍스트가 충분하다면 질문에 대한 설명 없이 정확한 SQL 쿼리를 생성해주세요.
        2. 제공된 컨텍스트가 충분하지 않을 때에는 쿼리를 생성할 수 없는 이유를 설명해주세요.
        3. 컨텍스트에서 테이블 리스트가 주어지면 그 중에서 가장 관련성 높은 테이블들을 사용해주세요.
        4. JOIN 구문을 사용할 경우, 반드시 테이블 별칭(alias)을 명시해 주세요. 
        5. Subquery의 depth가 2보다 큰 경우, CTE를 사용해주세요.
        6. 응답 전에 쿼리의 문법이 맞는지, 사용한 컬럼이 테이블에 존재하는지 한번 더 확인해주세요.
        """
    )

    agent = Agent(
        name="Assistant",
        instructions=instructions,
        mcp_servers=[mcp_server],
    )

    message = "평점 4.0 이상을 한 번 이라도 준 남성 유저가 총 유저 중 몇 퍼센트인지 알려줘"
    print("\n" + "-" * 40)
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)


async def main():
    async with MCPServerStdio(
        cache_tools_list=True,
        params={
            "command": "uv",
            "args": [
                "run",
                "--with",
                "mcp[cli]",
                "--with",
                "sqlalchemy",
                "--with",
                "trino",
                "mcp",
                "run",
                "/Users/dglee/Side/sql-helper/mcp_test/query.py"
            ]
        },
    ) as server:
        with trace(workflow_name="MCP AI Data Analyst"):
            await run(server)


if __name__ == "__main__":
    asyncio.run(main())
