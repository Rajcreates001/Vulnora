import asyncio, httpx
async def check_scan():
    async with httpx.AsyncClient() as client:
        resp = await client.get('http://localhost:8001/api/projects')
        projs = resp.json()['data']['projects']
        newest = projs[0]
        print('Newest project:', newest['name'], newest['id'])
        resp2 = await client.get(f"http://localhost:8001/api/scan-status/{newest['id']}")
        print('Status:', resp2.json())
asyncio.run(check_scan())
