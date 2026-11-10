import json
from pathlib import Path

from sqlmodel import Session, select

from app.models import Product, Review

DATA_FILE = Path(__file__).resolve().parent / "data" / "products.json"


def seed_if_empty(session: Session) -> bool:
    """Load the demo catalog if the products table is empty. Returns True if seeded."""
    exists = session.exec(select(Product).limit(1)).first()



    if exists:
        return False

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for item in payload["products"]:
        session.add(Product(**item))

    for item in payload["reviews"]:
        session.add(Review(**item))
    session.commit()
    return True













