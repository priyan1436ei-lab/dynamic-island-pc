import threading
import time
import urllib.request

class WeatherService:
    _cached_weather = "வானிலை: தகவல்களைப் பெறுகிறது..."
    _last_fetched = 0
    _is_fetching = False

    @classmethod
    def get_weather(cls):
        now = time.time()
        # Refresh every 15 minutes in background
        if now - cls._last_fetched > 900 and not cls._is_fetching:
            threading.Thread(target=cls._fetch_worker, daemon=True).start()
        return cls._cached_weather

    @classmethod
    def _fetch_worker(cls):
        cls._is_fetching = True
        try:
            req = urllib.request.Request(
                "https://wttr.in/?format=%C+%t",
                headers={"User-Agent": "curl/7.68.0"}
            )
            with urllib.request.urlopen(req, timeout=4) as res:
                text = res.read().decode("utf-8").strip()
                if text:
                    cls._cached_weather = f"🌤️ {text}"
                    cls._last_fetched = time.time()
        except Exception:
            if cls._last_fetched == 0:
                cls._cached_weather = "🌤️ வானிலை: 28°C (ஆஃப்லைன்)"
        finally:
            cls._is_fetching = False
