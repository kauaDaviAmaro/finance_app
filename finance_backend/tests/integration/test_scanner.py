from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import DailyScanResult, UserRole, User
from app.core.security import create_access_token


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_scanner_requires_pro(client: TestClient, db: Session, test_user: User):
    # USER (free) deve tomar 402
    headers = _auth_headers_for_user(test_user)
    resp = client.get("/stocks/scanner", headers=headers)
    assert resp.status_code == 402


def test_scanner_filters_and_returns_results(client: TestClient, db: Session, test_user_admin: User):
    # Popular snapshot com 3 tickers
    rows = [
        DailyScanResult(ticker="PETR4", last_price=30.12, rsi_14=28.5, macd_h=0.15, bb_upper=31.0, bb_lower=28.0),
        DailyScanResult(ticker="VALE3", last_price=60.05, rsi_14=35.0, macd_h=-0.20, bb_upper=62.0, bb_lower=58.0),
        DailyScanResult(ticker="MGLU3", last_price=2.50, rsi_14=25.0, macd_h=0.05, bb_upper=2.70, bb_lower=2.30),
    ]
    for r in rows:
        db.merge(r)
    db.commit()

    headers = _auth_headers_for_user(test_user_admin)

    # Filtro: RSI < 30 e MACD > 0 → espera PETR4 e MGLU3
    resp = client.get(
        "/stocks/scanner",
        params={"rsi_lt": 30, "macd_gt": 0, "sort": "rsi_asc"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    tickers = [row["ticker"] for row in data]
    assert "PETR4" in tickers and "MGLU3" in tickers
    assert "VALE3" not in tickers










