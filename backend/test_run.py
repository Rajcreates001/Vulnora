import asyncio
import os
from dotenv import load_dotenv

async def test():
    load_dotenv()
    print("Testing pipeline from start to finish...")
    
    # Needs a real project ID from db. Assuming one exists:
    from db.supabase_client import get_projects
    projs = await get_projects()
    if not projs:
        print("No projects.")
        return
        
    pid = projs[0]["id"]
    print(f"Targeting: {pid}")
    
    from graph.workflow import run_security_scan
    try:
        res = await run_security_scan(pid)
        print("Final Report Output:", type(res))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
