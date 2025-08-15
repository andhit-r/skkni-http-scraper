import asyncio
import click
from app.core.db import SessionLocal, init_db
from app.db import crud
from app.repositories.skkni_repository import SkkniRepository

@click.group()
def cli():
    pass

@cli.command("ingest")
@click.option("--from-page", default=1, type=int)
@click.option("--to-page", default=10, type=int)
@click.option("--limit", default=50, type=int)
def ingest(from_page: int, to_page: int, limit: int):
    """Bulk fetch documents & units and store to DB."""
    init_db()
    asyncio.run(_run_ingest(from_page, to_page, limit))

async def _run_ingest(from_page: int, to_page: int, limit: int):
    repo = SkkniRepository()

    docs = await repo.fetch_documents(page_from=from_page, page_to=to_page, limit=limit)
    units = await repo.fetch_units(page_from=from_page, page_to=to_page, limit=limit)

    with SessionLocal() as db:
        crud.upsert_documents(db, docs)
        crud.upsert_units(db, units)
        db.commit()
    click.echo("Ingest done.")

if __name__ == "__main__":
    cli()
