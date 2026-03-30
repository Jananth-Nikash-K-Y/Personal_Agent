"""
Web tools — search, news, weather, and monitoring.
"""
import os
import json
import subprocess
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def web_search(query: str) -> str:
    """Search the web using Tavily or fallback to DuckDuckGo."""
    from config import TAVILY_API_KEY
    if TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            results = client.search(query, max_results=5, include_answer=True)
            return json.dumps({
                "status": "success", "query": query, "answer": results.get("answer", ""),
                "results": [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")[:500]} for r in results.get("results", [])]
            })
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
    try:
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        result = subprocess.run(["curl", "-s", f"https://r.jina.ai/https://lite.duckduckgo.com/lite/?q={encoded}"], capture_output=True, text=True, timeout=15)
        return json.dumps({"status": "success", "query": query, "source": "jina-duckduckgo", "raw_text": result.stdout.strip()[:3000]})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def get_top_news(category: str = "general", country: str = "India") -> str:
    """Fetch today's top news headlines."""
    from config import TAVILY_API_KEY
    today = datetime.now(tz=timezone.utc).strftime("%B %d, %Y")
    query = f"top {category} news today {today} {country}"
    if category.lower() in ["business", "general"]:
        query += " -school -assembly -\"Class 10\" -board"
    if TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            results = client.search(query, max_results=7, topic="news", include_answer=True)
            headlines = [{"title": r.get("title", ""), "url": r.get("url", ""), "source": r.get("url", "").split("/")[2] if r.get("url") else "", "snippet": r.get("content", "")[:300]} for r in results.get("results", [])]
            return json.dumps({"status": "success", "date": today, "category": category, "country": country, "summary": results.get("answer", ""), "headlines": headlines})
        except Exception as e:
            logger.warning(f"Tavily news search failed: {e}")
    return await web_search(f"top {category} news {today}")

async def get_weather(location: str) -> str:
    """Get weather information using wttr.in."""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(location)
        result = subprocess.run(["curl", "-s", f"https://wttr.in/{encoded}?format=j1"], capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        current = data.get("current_condition", [{}])[0]
        return json.dumps({
            "status": "success", "location": location, "temperature_c": current.get("temp_C"),
            "temperature_f": current.get("temp_F"), "feels_like_c": current.get("FeelsLikeC"),
            "humidity": current.get("humidity"), "description": current.get("weatherDesc", [{}])[0].get("value", ""),
            "wind_speed_kmph": current.get("windspeedKmph"), "wind_direction": current.get("winddir16Point"),
            "visibility_km": current.get("visibility"), "uv_index": current.get("uvIndex"),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def add_web_monitor(url: str, label: str, selector: str = None, threshold: str = None) -> str:
    """Set up a monitor to watch a webpage for changes."""
    from core.history import history
    try:
        history.add_web_monitor(url, label, selector, threshold)
        return json.dumps({"status": "success", "message": f"Web monitor added for {label} at {url}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
