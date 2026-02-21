import asyncio
import os
from agents.parser_agent import ParserAgent

async def test_parser():
    print("Testing Parser Agent...")
    try:
        agent = ParserAgent()
        
        state = {
            "project_id": "test_id",
            "files": [],
            "errors": [],
            "ast_data": []
        }
        res = await agent.run(state)
        print("Success:", res)
    except Exception as e:
        print("CRASH:", str(e))

if __name__ == "__main__":
    asyncio.run(test_parser())
