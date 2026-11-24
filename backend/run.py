"""
DockScope Backend Server Entrypoint

Ensures Windows-compatible asyncio SelectorEventLoop is active for psycopg async PostgreSQL driver.
Can be executed directly via:
    python run.py
or via:
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --loop asyncio:SelectorEventLoop
"""
import sys
import asyncio

if sys.platform == "win32":
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    import uvicorn
    loop_target = "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, loop=loop_target)
