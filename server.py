import sys
import asyncio
import uvicorn
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=False, # Set ke False untuk kestabilan Playwright di Windows
        loop="asyncio"
    )