from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.db.session import Base
import app.models.models  # noqa: F401  (register all tables on Base.metadata)

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True,
                      compare_type=True, render_as_batch="sqlite" in settings.DATABASE_URL)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, compare_type=True,
                          render_as_batch=conn.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
