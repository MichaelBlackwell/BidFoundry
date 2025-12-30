#!/usr/bin/env python
"""Server startup script."""

# Load environment variables BEFORE importing anything else
from dotenv import load_dotenv
load_dotenv()

import uvicorn

from server.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
