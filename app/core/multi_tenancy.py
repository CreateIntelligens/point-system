from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def set_search_path(session: AsyncSession, schema: str):
    """
    Set PostgreSQL schema (search_path) for the current session.
    """
    await session.execute(text(f'SET search_path TO "{schema}", public'))
