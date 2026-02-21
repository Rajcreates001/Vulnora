import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

async def check():
    from db.supabase_client import get_projects, get_project_files
    projects = await get_projects()
    print('Recent projects:')
    for p in projects[:5]:
        files = await get_project_files(p['id'])
        print(f"- {p['name']} ({p['id']}) - status: {p.get('scan_status')}")
        print(f"  -> {len(files)} files stored in DB")

asyncio.run(check())
