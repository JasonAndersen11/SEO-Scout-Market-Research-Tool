import json
import threading
from pathlib import Path

_CACHE_FILE = Path(__file__).parent.parent.parent / "city_result_cache.json"
_lock = threading.Lock()


def _load() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(cache: dict) -> None:
    _CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _key(keyword: str, city: str, state: str) -> str:
    return f"{keyword.lower().strip()}|{city.lower().strip()}|{state.upper().strip()}"


def get(keyword: str, city: str, state: str) -> str | None:
    with _lock:
        return _load().get(_key(keyword, city, state))


def put(keyword: str, city: str, state: str, result: str) -> None:
    with _lock:
        cache = _load()
        cache[_key(keyword, city, state)] = result
        _save(cache)


def size() -> int:
    with _lock:
        return len(_load())
