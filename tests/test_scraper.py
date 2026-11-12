from pathlib import Path
import pytest
from app.scraper import parse_price, extract_price, ScrapeError, fetch_price

@pytest.mark.parametrize(('raw', 'expected'), [('2 499,99 zł', '2499.99'), ('$1,299.99', '1299.99'), ('€1.299,99', '1299.99'), ('99.95 PLN', '99.95')])
def test_price_formats(raw, expected):
    assert str(parse_price(raw)) == expected

def test_fixture_html():
    html = (Path(__file__).parent / 'fixtures' / 'product.html').read_text(encoding='utf-8')
    assert str(extract_price(html, '.product-price')) == '2499.99'

def test_missing_selector():
    with pytest.raises(ScrapeError, match='not found'):
        extract_price('<p>hello</p>', '.price')

def test_invalid_url():
    with pytest.raises(ScrapeError, match='HTTP'):
        fetch_price('file:///etc/passwd', '.price')
