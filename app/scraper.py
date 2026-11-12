"""Scrape publicly accessible HTML using a per-product CSS selector.

Respect robots.txt, website terms and rate limits. This tool does not bypass anti-bot systems.
"""
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

class ScrapeError(Exception):
    pass

def parse_price(text: str) -> Decimal:
    """Parse typical PLN/EUR/USD prices, including 1 299,99 and 1,299.99."""
    cleaned = re.sub(r'[^\d,.\s\u00a0]', '', text).replace('\u00a0', '').replace(' ', '').strip()
    if not cleaned:
        raise ScrapeError('No numeric price found')
    if ',' in cleaned and '.' in cleaned:
        decimal_mark = ',' if cleaned.rfind(',') > cleaned.rfind('.') else '.'
        grouping_mark = '.' if decimal_mark == ',' else ','
        cleaned = cleaned.replace(grouping_mark, '').replace(decimal_mark, '.')
    elif ',' in cleaned:
        parts = cleaned.split(',')
        cleaned = ''.join(parts[:-1]) + ('.' + parts[-1] if len(parts[-1]) in (1, 2) else parts[-1])
    elif '.' in cleaned:
        parts = cleaned.split('.')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3):
            cleaned = ''.join(parts)
    try:
        value = Decimal(cleaned).quantize(Decimal('0.01'))
    except InvalidOperation as exc:
        raise ScrapeError(f'Cannot parse price: {text!r}') from exc
    if value < 0 or not value.is_finite():
        raise ScrapeError('Price must be a nonnegative finite number')
    return value

def extract_price(html: str, selector: str) -> Decimal:
    try:
        element = BeautifulSoup(html, 'html.parser').select_one(selector)
    except Exception as exc:
        raise ScrapeError(f'Invalid CSS selector: {selector}') from exc
    if element is None:
        raise ScrapeError(f'Price element not found for selector {selector!r}')
    return parse_price(element.get_text(' ', strip=True))

def fetch_price(url: str, selector: str, *, session=None) -> Decimal:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ScrapeError('A valid HTTP(S) URL is required')
    client = session or requests
    try:
        response = client.get(url, timeout=15, headers={'User-Agent': 'PriceWatchPortfolio/1.0 (educational; respectful crawling)'})
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapeError(f'HTTP request failed: {exc}') from exc
    return extract_price(response.text, selector)
