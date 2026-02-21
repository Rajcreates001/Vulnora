import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

async def check():
    from db.supabase_client import get_projects, get_project_files
    projects = await get_projects()
    with open('results.txt', 'w', encoding='utf-8') as f:
        f.write('Recent projects:\n')
        for p in projects[:3]:
            files = await get_project_files(p['id'])
            f.write(f"Project: {p['name']} ({p['id']}) Status: {p.get('scan_status')}\n")
            f.write(f"Files in DB: {len(files)}\n")

asyncio.run(check())
