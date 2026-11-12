import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import Base, make_engine, make_session_factory
from .models import Product, PriceObservation
from .services import add_product, check_product, latest_prices
from .analytics import history_frame, summary
from .scraper import ScrapeError

log = logging.getLogger('pricewatch')

def parser():
    p = argparse.ArgumentParser(prog='pricewatch', description='Track public web page prices with configurable CSS selectors')
    p.add_argument('--db', help='SQLAlchemy database URL (default: pricewatch.db in project folder)')
    sub = p.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add', help='Add a product')
    for key in ('name', 'url', 'selector'):
        add.add_argument(f'--{key}', required=True)
    add.add_argument('--target', help='Target price')
    add.add_argument('--currency', default='PLN')
    sub.add_parser('list', help='List products and latest prices')
    check = sub.add_parser('check', help='Check one or all products')
    check.add_argument('--id', type=int)
    check.add_argument('--delay', type=float, default=2.0, help='Seconds between requests when checking all products')
    for command in ('history', 'stats', 'remove'):
        action = sub.add_parser(command)
        action.add_argument('id', type=int)
        if command == 'history':
            action.add_argument('--csv', dest='csv_path', help='Export history to CSV')
    return p

def run(argv=None):
    args = parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    if args.command == 'check' and args.delay < 0:
        print('Error: --delay must be nonnegative', file=sys.stderr)
        return 2
    engine = make_engine(args.db)
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as db:
        try:
            if args.command == 'add':
                p = add_product(db, name=args.name, url=args.url, selector=args.selector, target_price=args.target, currency=args.currency)
                print(f'Added #{p.id}: {p.name} ({p.currency})')
            elif args.command == 'list':
                rows = latest_prices(db)
                if not rows:
                    print('No products. Use "add" to register one.')
                for p, obs in rows:
                    latest = str(obs.price) if obs else 'not checked'
                    print(f'#{p.id} | {p.name} | latest: {latest} {p.currency} | target: {p.target_price or "none"} | {p.url}')
            elif args.command == 'check':
                products = [db.get(Product, args.id)] if args.id else db.scalars(select(Product).order_by(Product.id)).all()
                if not products or products == [None]:
                    print('No matching products.', file=sys.stderr)
                    return 1
                failures = 0
                for i, p in enumerate(products):
                    if i:
                        time.sleep(args.delay)
                    try:
                        obs, reached = check_product(db, p)
                        print(f'#{p.id} {p.name}: {obs.price} {p.currency}' + (' | TARGET REACHED' if reached else ''))
                    except ScrapeError as exc:
                        failures += 1
                        log.error('Could not check #%s: %s', p.id, exc)
                return 1 if failures else 0
            elif args.command == 'history':
                p = db.get(Product, args.id)
                if p is None:
                    print('Product not found.', file=sys.stderr)
                    return 1
                frame = history_frame(db, p.id)
                if frame.empty:
                    print('No observations yet.')
                else:
                    print(frame.to_string(index=False))
                if args.csv_path:
                    frame.to_csv(args.csv_path, index=False)
                    print(f'Exported to {args.csv_path}')
            elif args.command == 'stats':
                p = db.get(Product, args.id)
                if p is None:
                    print('Product not found.', file=sys.stderr)
                    return 1
                result = summary(db, p.id)
                if result is None:
                    print('No observations yet.')
                else:
                    for key, value in result.items():
                        print(f'{key}: {value}')
            elif args.command == 'remove':
                p = db.get(Product, args.id)
                if p is None:
                    print('Product not found.', file=sys.stderr)
                    return 1
                db.delete(p)
                db.commit()
                print(f'Removed product #{args.id} and its history.')
        except (ValueError, IntegrityError) as exc:
            db.rollback()
            print(f'Error: {exc}', file=sys.stderr)
            return 2
    return 0
