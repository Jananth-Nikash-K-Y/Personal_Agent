"""
Finance tools — market data, Indian stocks, and expense tracking.
"""
import os
import json
import subprocess
import logging
from config import INDIAN_API_KEY

logger = logging.getLogger(__name__)

PRECIOUS_METALS = {"gold", "silver", "platinum", "palladium"}
METAL_QUERIES = {
    "gold":     "gold price today per gram India 24k 22k site:goodreturns.in OR site:businesstoday.in",
    "silver":   "silver price today per gram India site:goodreturns.in OR site:businesstoday.in",
    "platinum": "platinum price today per gram India site:goodreturns.in OR site:businesstoday.in",
    "palladium":"palladium price today per gram India",
}
INDIA_STOCK_API = "https://indian-stock-market-api.onrender.com"

async def _get_usd_inr() -> float:
    """Fetch live USD/INR exchange rate using yfinance."""
    try:
        import yfinance as yf
        t = yf.Ticker("USDINR=X")
        h = t.history(period="1d")
        return float(h["Close"].iloc[-1]) if not h.empty else 85.0
    except Exception:
        return 85.0

async def get_market_data(symbol: str) -> str:
    """Get real-time market data for stocks and metals."""
    sym_lower = symbol.lower().strip()
    if sym_lower in PRECIOUS_METALS:
        if INDIAN_API_KEY:
            try:
                base_url = "https://indianapi.in"
                result = subprocess.run(["curl", "-s", "-H", f"x-api-key: {INDIAN_API_KEY}", f"{base_url}/commodities?name={sym_lower.upper()}"], capture_output=True, text=True, timeout=10)
                data = json.loads(result.stdout) if result.stdout else {}
                if data and "error" not in str(data).lower():
                    item = data if not isinstance(data, list) else data[0]
                    return json.dumps({"status": "success", "asset": sym_lower.upper(), "currency": "INR", "price": item.get("tradePrice") or item.get("lastPrice") or item.get("price"), "change": item.get("change"), "percent_change": item.get("pChange") or item.get("percentChange"), "data_source": "IndianAPI.in (Official)"})
            except Exception: pass
        query = METAL_QUERIES.get(sym_lower, f"{sym_lower} price today per gram India")
        try:
            from tavily import TavilyClient
            tkey = os.getenv("TAVILY_API_KEY")
            if tkey:
                tc = TavilyClient(api_key=tkey)
                result = tc.search(query=query, search_depth="advanced", max_results=3, include_answer=True)
                if result.get("answer"):
                    return json.dumps({"status": "success", "asset": sym_lower, "pricing_region": "India", "data": result.get("answer"), "sources": [r.get("url", "") for r in result.get("results", [])]})
        except Exception as e: return json.dumps({"status": "error", "message": f"Metal lookup failed: {str(e)}"})

    is_indian = sym_lower.endswith(".ns") or sym_lower.endswith(".bo") or (not "." in sym_lower and len(sym_lower) <= 15)
    if is_indian:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        if INDIAN_API_KEY:
            try:
                result = subprocess.run(["curl", "-s", "-H", f"x-api-key: {INDIAN_API_KEY}", f"https://indianapi.in/stock?name={clean}"], capture_output=True, text=True, timeout=8)
                raw = json.loads(result.stdout) if result.stdout else {}
                if raw and "error" not in str(raw).lower():
                    return json.dumps({"status": "success", "symbol": clean, "currency": "INR", "last_price": raw.get("currentPrice", {}).get("NSE") or raw.get("price"), "change": raw.get("percentChange"), "data_source": "IndianAPI.in (Pro)"})
            except Exception: pass
        try:
            result = subprocess.run(["curl", "-s", f"{INDIA_STOCK_API}/stock?name={clean}&series=EQ"], capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout) if result.stdout else {}
            if data and "error" not in str(data).lower():
                price_info = data if not isinstance(data, list) else data[0]
                return json.dumps({"status": "success", "symbol": clean, "currency": "INR", "last_price": price_info.get("lastPrice") or price_info.get("last"), "change": price_info.get("change"), "percent_change": price_info.get("pChange"), "data_source": "NSE India (Proxy)"})
        except Exception: pass

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period="5d")
        if not hist.empty:
            info = ticker.info
            currency = info.get("currency", "USD")
            cp = float(hist["Close"].iloc[-1])
            pc = float(hist["Close"].iloc[-2]) if len(hist) > 1 else cp
            if currency == "USD":
                fx = await _get_usd_inr()
                currency = "INR (converted)"
                cp *= fx; pc *= fx
            return json.dumps({"status": "success", "symbol": symbol.upper(), "name": info.get("shortName", symbol), "currency": currency, "current_price": round(cp, 2), "change": round(cp - pc, 2), "percent_change_today": round(((cp - pc) / pc) * 100, 2) if pc else 0})
    except Exception as e: return json.dumps({"status": "error", "message": f"Error fetching {symbol}: {str(e)}"})
    return json.dumps({"status": "error", "message": f"No data found for: {symbol}"})

async def get_indian_analysis(symbol: str) -> str:
    """Get deep financial analysis for Indian stocks."""
    if not INDIAN_API_KEY: return json.dumps({"status": "error", "message": "IndianAPI.in key missing."})
    clean = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    try:
        result = subprocess.run(["curl", "-s", "-H", f"x-api-key: {INDIAN_API_KEY}", f"https://indianapi.in/stock?name={clean}"], capture_output=True, text=True, timeout=10)
        raw = json.loads(result.stdout) if result.stdout else {}
        if not raw or "error" in str(raw).lower(): return json.dumps({"status": "error", "message": f"Not found: {clean}"})
        trimmed = {"symbol": clean, "companyName": raw.get("companyName"), "industry": raw.get("industry"), "current_price": raw.get("currentPrice"), "keyMetrics": raw.get("keyMetrics"), "analystView": raw.get("analystView"), "recosBar": raw.get("recosBar"), "shareholding": raw.get("shareholding")}
        return json.dumps({"status": "success", "data": trimmed})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def log_expense(amount: float, description: str, category: str = "General", merchant: str = None, date: str = None, currency: str = "INR") -> str:
    """Log a personal expense."""
    from core.history import history
    try:
        expense_id = history.add_expense(amount, category, description, merchant, date, currency)
        return json.dumps({"status": "success", "message": f"Expense logged (ID {expense_id}): {amount} {currency} for {description}"})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

async def get_expense_summary(limit: int = 20) -> str:
    """Get a list of recent expenses."""
    from core.history import history
    try:
        expenses = history.get_expenses(limit)
        return json.dumps({"status": "success", "count": len(expenses), "expenses": expenses})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})
