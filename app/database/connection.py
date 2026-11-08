
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import Settings


settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    """
    Disponibiliza uma sessão do banco para as rotas.
    Garante o fechamento da conexão após a requisição.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
