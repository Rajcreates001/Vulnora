import asyncio
from db.supabase_client import get_projects, get_agent_logs

async def check():
    projs = await get_projects()
    if not projs: return
    p = projs[0]
    logs = await get_agent_logs(p['id'])
    with open('db_output_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(p['name'] + ' ' + p['scan_status'] + '\n')
        for l in logs:
            f.write(f"[{l['agent_name']}] {l['log_type']}: {l['message']}\n")

asyncio.run(check())
