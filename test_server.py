import asyncio
from remote.server import mcp

async def main():
    print("Testing custom route...")
    # FastMCP creates a Starlette/FastAPI app internally.
    # Let's see if we can get the ASGI app.
    app = mcp._app
    from starlette.testclient import TestClient
    client = TestClient(app)
    response = client.get('/r/L41mMbiVvFU', allow_redirects=False)
    print("Status:", response.status_code)
    print("Headers:", response.headers)

asyncio.run(main())
