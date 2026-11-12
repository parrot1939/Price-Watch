from decimal import Decimal
from app.services import add_product, check_product, latest_prices
from app.analytics import summary, history_frame
from app.models import Product

def test_add_and_list(db):
    p = add_product(db, name='Demo', url='https://example.com/item', selector='.price', target_price='100')
    assert p.id > 0
    assert latest_prices(db)[0][1] is None

def test_check_and_target(db):
    p = add_product(db, name='Demo', url='https://example.com/item', selector='.price', target_price='100')
    obs, reached = check_product(db, p, fetcher=lambda url, selector: Decimal('89.99'))
    assert reached is True
    assert obs.price == Decimal('89.99')
    assert summary(db, p.id)['minimum'] == 89.99
    assert len(history_frame(db, p.id)) == 1

def test_reject_invalid_target(db):
    import pytest
    with pytest.raises(ValueError):
        add_product(db, name='Demo', url='https://example.com/item', selector='.price', target_price='-2')

def test_delete_cascades(db):
    p = add_product(db, name='Demo', url='https://example.com/item', selector='.price')
    check_product(db, p, fetcher=lambda *_: Decimal('10.00'))
    db.delete(p)
    db.commit()
    assert db.get(Product, p.id) is None
    assert history_frame(db, p.id).empty
