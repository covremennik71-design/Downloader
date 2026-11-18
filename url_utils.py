"""Strict YouTube URL normalization for the standalone application."""
from urllib.parse import urlsplit, urlunsplit, parse_qs
import re
_ALLOWED={"youtube.com","www.youtube.com","m.youtube.com","music.youtube.com","youtu.be","www.youtu.be"}
_ID=re.compile(r"^[A-Za-z0-9_-]{11}$")
def normalize_youtube_url(value: str) -> str:
    if not isinstance(value,str) or not value.strip(): raise ValueError("Введите ссылку на видео.")
    value=value.strip()
    if value.startswith("//"): raise ValueError("Некорректная ссылка YouTube.")
    try: parsed=urlsplit(value if "://" in value else "https://"+value); port=parsed.port
    except ValueError as exc: raise ValueError("Некорректный адрес URL.") from exc
    if parsed.scheme.lower() not in {"http","https"}: raise ValueError("Разрешены только HTTP и HTTPS.")
    host=(parsed.hostname or "").lower().rstrip(".")
    if host not in _ALLOWED or parsed.username or parsed.password: raise ValueError("Разрешены только корректные ссылки YouTube.")
    if port is not None and port not in {80,443}: raise ValueError("Нестандартный порт не поддерживается.")
    if host.endswith("youtu.be"): video_id=parsed.path.strip("/").split("/")[0]
    elif parsed.path=="/watch": video_id=parse_qs(parsed.query).get("v",[""])[0]
    else:
        parts=[p for p in parsed.path.split("/") if p]
        video_id=parts[1] if len(parts)==2 and parts[0] in {"embed","shorts","live","v"} else ""
    if not _ID.fullmatch(video_id): raise ValueError("Не удалось определить идентификатор видео YouTube.")
    return urlunsplit((parsed.scheme.lower(),parsed.netloc,parsed.path,parsed.query,""))
