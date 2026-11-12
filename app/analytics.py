import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import PriceObservation

def history_frame(db: Session, product_id: int) -> pd.DataFrame:
    observations = db.scalars(select(PriceObservation).where(PriceObservation.product_id == product_id).order_by(PriceObservation.checked_at, PriceObservation.id)).all()
    return pd.DataFrame([{'timestamp': o.checked_at.isoformat(), 'price': float(o.price)} for o in observations], columns=['timestamp', 'price'])

def summary(db: Session, product_id: int) -> dict | None:
    frame = history_frame(db, product_id)
    if frame.empty:
        return None
    prices = frame['price']
    return {'count': len(frame), 'latest': float(prices.iloc[-1]), 'minimum': float(prices.min()), 'maximum': float(prices.max()), 'average': round(float(prices.mean()), 2), 'change': round(float(prices.iloc[-1] - prices.iloc[0]), 2)}
