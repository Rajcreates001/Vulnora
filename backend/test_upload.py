import asyncio, httpx

async def test_upload():
    print('Starting upload...')
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Upload repo
        resp = await client.post('http://localhost:8001/api/upload-repo', data={
            'project_name': 'AquaIntel_ThreadTest',
            'repo_url': 'https://github.com/Rajcreates001/AquaIntel'
        })
        print('Upload response code:', resp.status_code)
        if resp.status_code != 200:
            print('Error:', resp.text)
            return

        data = resp.json()
        project_id = data['data']['project_id']
        print(f'Got project_id: {project_id}')

        # 2. Start scan
        print('Starting scan...')
        resp2 = await client.post(f'http://localhost:8001/api/scan/{project_id}')
        print('Scan response code:', resp2.status_code)
        print('Scan data:', resp2.text)

asyncio.run(test_upload())
