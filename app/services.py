from decimal import Decimal, InvalidOperation
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Product, PriceObservation
from .scraper import fetch_price

def money(value: str | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    try:
        result = Decimal(str(value)).quantize(Decimal('0.01'))
    except InvalidOperation as exc:
        raise ValueError('Invalid amount') from exc
    if not result.is_finite() or result < 0:
        raise ValueError('Amount must be finite and nonnegative')
    return result

def add_product(db: Session, *, name: str, url: str, selector: str, currency: str = 'PLN', target_price=None) -> Product:
    if not name.strip() or not selector.strip():
        raise ValueError('Name and selector cannot be empty')
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Provide a valid HTTP(S) URL')
    currency = currency.upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError('Currency must be a three-letter code')
    product = Product(name=name.strip(), url=url, selector=selector, currency=currency, target_price=money(target_price))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def check_product(db: Session, product: Product, *, fetcher=fetch_price):
    price = fetcher(product.url, product.selector)
    observation = PriceObservation(product_id=product.id, price=price)
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation, product.target_price is not None and price <= product.target_price

def latest_prices(db: Session):
    products = db.scalars(select(Product).order_by(Product.id)).all()
    rows = []
    for product in products:
        last = db.scalars(select(PriceObservation).where(PriceObservation.product_id == product.id).order_by(PriceObservation.checked_at.desc(), PriceObservation.id.desc()).limit(1)).first()
        rows.append((product, last))
    return rows
