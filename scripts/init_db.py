#!/usr/bin/env python
"""Initialize the database and create all tables."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from server.models.database import init_db, engine
from server.config import settings


async def main():
    """Initialize the database."""
    print(f"Database URL: {settings.database_url}")

    # Ensure data directory exists
    db_path = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("Creating database tables...")
    await init_db()
    print("Database initialized successfully!")

    # Clean up
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
