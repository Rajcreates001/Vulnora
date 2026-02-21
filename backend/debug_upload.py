import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv('.env')

async def debug_upload():
    print("Starting debug upload...")
    from services.upload_service import handle_github_upload
    try:
        res = await handle_github_upload("https://github.com/Rajcreates001/AquaIntel", "AquaIntel_Debug")
        print("Upload success:", res)
    except Exception as e:
        print("Upload failed:", e)

asyncio.run(debug_upload())
