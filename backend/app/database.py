"""
Database Connection Module

This module sets up the SQLAlchemy async database connection.
It provides the engine, session factory, and base class for models.

Usage:
    from app.database import get_db, engine, Base
    
    # In FastAPI dependency
    async def some_endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


def get_database_url() -> str:
    """
    Convert the database URL to async format if needed.
    
    SQLite URLs need to use 'sqlite+aiosqlite://' for async support.
    
    Returns:
        str: The async-compatible database URL
    """
    url = settings.DATABASE_URL
    
    # Convert sqlite:/// to sqlite+aiosqlite:/// for async support
    if url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    # Convert postgres URLs to asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    return url


# Create async engine
# echo=True logs all SQL statements (helpful for debugging, disable in production)
engine = create_async_engine(
    get_database_url(),
    echo=False,  # Set to True to see SQL queries in console
)

# Create async session factory
# expire_on_commit=False prevents attributes from being expired after commit
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias for direct session access (used in startup tasks)
async_session = async_session_maker


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    All database models should inherit from this class.
    This provides the declarative mapping functionality.
    """
    pass


async def create_tables() -> None:
    """
    Create all database tables.
    
    This function creates all tables defined by models that inherit from Base.
    Called during application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """
    Dependency that provides a database session.
    
    This is a generator that creates a new session for each request
    and closes it when the request is complete.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
