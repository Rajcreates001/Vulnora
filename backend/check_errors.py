import asyncio, httpx, json
async def check_errors():
    async with httpx.AsyncClient() as client:
        resp = await client.get('http://localhost:8001/api/projects')
        projs = resp.json()['data']['projects']
        if not projs:
            print('No projects found')
            return
            
        newest = projs[0]
        print('Newest project:', newest['name'], newest['id'])
        print('Status:', newest.get('scan_status'))
        
        # Check logs
        resp2 = await client.get(f"http://localhost:8001/api/scan-logs/{newest['id']}")
        logs = resp2.json().get('logs', [])
        print('\n--- RECENT LOGS ---')
        for log in logs:
            if log.get('log_type') == 'error' or log.get('log_type') == 'warning':
                print(f"[{log.get('agent_name')}] {log.get('log_type')}: {log.get('message')}")
            elif 'Error:' in log.get('message', ''):
                print(f"[{log.get('agent_name')}] error-text: {log.get('message')}")
asyncio.run(check_errors())
