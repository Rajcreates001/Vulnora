import asyncio
import httpx
import time

async def poll_status(project_id):
    async with httpx.AsyncClient() as client:
        # Start scan
        print('Starting scan...')
        resp = await client.post(
            'http://localhost:8000/api/start-scan',
            json={'project_id': project_id, 'force': True}
        )
        print('Start scan response:', resp.status_code, resp.text[:100])
        
        # Poll status
        for _ in range(60):
            try:
                res = await client.get(f'http://localhost:8000/api/scan-status/{project_id}')
                data = res.json()
                if not data.get('success'):
                    print('Poll failed:', data)
                    continue
                d = data.get('data', {})
                print(f"[{time.strftime('%X')}] Status: {d.get('status')} | Agent: {d.get('current_agent')} | Completed: {len(d.get('agents_completed', []))}")
                
                if d.get('status') in ['completed', 'failed']:
                    print('Finished polling. Final state:', d.get('status'))
                    break
            except Exception as e:
                print('Error polling:', e)
            await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(poll_status('d7ec2c61-dcc6-4df7-9384-6328a055ebb1'))
