from __future__ import annotations

from html.parser import HTMLParser
from functools import partial
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
import ipaddress
import os
import socket
import subprocess
import sys

import requests
from playwright.sync_api import sync_playwright, Error as PlaywrightError

from .tools import AITool


class WebAITool(AITool):
    """Базовый класс веб-инструментов с их OpenAI JSON-схемами."""

    @property
    def name(self) -> str:
        raise NotImplementedError("У каждого веб-инструмента должно быть собственное имя.")

    @property
    def description(self) -> str:
        raise NotImplementedError("У каждого веб-инструмента должно быть собственное описание.")

    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError("У каждого веб-инструмента должен быть свой execute().")

    def parameters_schema(self) -> dict[str, Any]:
        schemas: dict[str, dict[str, Any]] = {
            "web_search": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "edge_search": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "engine": {
                        "type": "string",
                        "enum": ["bing", "google", "brave", "duckduckgo"],
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "browser_open": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "fallback_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
            "browser_read": {
                "type": "object",
                "properties": {"max_chars": {"type": "integer"}},
                "additionalProperties": False,
            },
            "browser_type": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["selector", "text"],
                "additionalProperties": False,
            },
            "browser_click": {
                "type": "object",
                "properties": {"selector": {"type": "string"}},
                "required": ["selector"],
                "additionalProperties": False,
            },
        }
        return schemas.get(
            self.name,
            {"type": "object", "properties": {}, "additionalProperties": False},
        )


# ============================================================
# SETTINGS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BROWSER_PROFILE = PROJECT_ROOT / "data" / "browser_profile"

DEFAULT_SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://search.sapti.me",
    "https://searx.ononoki.org",
    "https://priv.au",
    "https://opnxng.com",
]

# Можно переопределить список через переменную окружения SEARXNG_INSTANCES.
SEARXNG_INSTANCES = [
    item.strip().rstrip("/")
    for item in os.getenv(
        "SEARXNG_INSTANCES", ",".join(DEFAULT_SEARXNG_INSTANCES)
    ).split(",")
    if item.strip()
]

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
)

BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").strip()


# ============================================================
# URL VALIDATION / SSRF MITIGATION
# ============================================================

def _validate_public_url(url: str) -> str:
    """Allow public HTTP(S) URLs and reject localhost/private IP addresses."""
    if not isinstance(url, str):
        raise ValueError("URL должен быть строкой.")

    url = url.strip()
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError(f"Некорректный URL: {error}") from error

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError("Разрешены только HTTP и HTTPS.")
    if not host:
        raise ValueError("В URL отсутствует имя хоста.")
    if parsed.username or parsed.password:
        raise ValueError("URL с данными авторизации запрещён.")

    host = host.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host == "localhost.localdomain":
        raise ValueError("Доступ к localhost запрещён.")

    port = port or (443 if scheme == "https" else 80)
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            addresses = list({ipaddress.ip_address(record[4][0]) for record in records})
        except (socket.gaierror, OSError, ValueError) as error:
            raise ValueError(f"Не удалось определить IP хоста {host!r}.") from error

    if not addresses:
        raise ValueError("IP-адрес хоста не найден.")
    if any(not address.is_global for address in addresses):
        raise ValueError("Доступ к локальным или непубличным IP запрещён.")
    return url


def _safe_result_url(url: str) -> str | None:
    try:
        return _validate_public_url(url)
    except (ValueError, TypeError):
        return None


def _clean_result(title: Any, url: Any, snippet: Any = "") -> dict[str, str] | None:
    title = " ".join(str(title or "").split()).strip()
    snippet = " ".join(str(snippet or "").split()).strip()
    safe_url = _safe_result_url(str(url or "").strip())
    if not title or not safe_url:
        return None
    return {"title": title[:500], "url": safe_url, "snippet": snippet[:1200]}


def _request_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
):
    # Redirects stay disabled: redirects should be validated explicitly before following.
    return requests.get(
        _validate_public_url(url),
        params=params,
        headers=headers or {"User-Agent": USER_AGENT},
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        allow_redirects=False,
    )


# ============================================================
# HTML SEARCH RESULT PARSER
# ============================================================

class _SearchHTMLParser(HTMLParser):
    """Extract common DuckDuckGo, Bing and some generic result links."""

    RESULT_CLASSES = {"result__a", "result-link", "result-title", "result__title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self.current_result: dict[str, str] | None = None
        self.capture_title = False
        self.bing_result_depth = 0
        self.bing_heading_depth = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        href = attr.get("href")

        if tag == "li" and "b_algo" in classes:
            self.bing_result_depth += 1

        if self.bing_result_depth and tag == "h2":
            self.bing_heading_depth += 1

        # Bing results: the target link is usually the first anchor inside h2.
        if self.bing_result_depth and self.bing_heading_depth and tag == "a" and href:
            self.current_result = {"title": "", "url": href, "snippet": ""}
            self.capture_title = True
            return

        is_result_link = tag == "a" and href and bool(classes.intersection(self.RESULT_CLASSES))
        if is_result_link:
            self.current_result = {"title": "", "url": href, "snippet": ""}
            self.capture_title = True

    def handle_data(self, data):
        if self.capture_title and self.current_result is not None:
            self.current_result["title"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.capture_title and self.current_result is not None:
            title = " ".join(self.current_result["title"].split()).strip()
            url = self.current_result["url"].strip()
            if title and url:
                self.results.append({"title": title, "url": url, "snippet": ""})
            self.current_result = None
            self.capture_title = False

        if tag == "h2" and self.bing_heading_depth:
            self.bing_heading_depth -= 1
        if tag == "li" and self.bing_result_depth:
            self.bing_result_depth -= 1


# ============================================================
# CAPTCHA DETECTION (NO AUTOMATIC BYPASS)
# ============================================================

CAPTCHA_MARKERS = (
    "captcha",
    "verify you are human",
    "verify that you are human",
    "prove you are human",
    "unusual traffic",
    "security check",
    "checking your browser",
    "challenge-platform",
    "robot check",
)


class CaptchaDetectedError(RuntimeError):
    """The site requires a manual verification step."""


def _detect_captcha(title: str, text: str, url: str) -> bool:
    content = f"{title}\n{text[:12000]}\n{url}".lower()
    return any(marker in content for marker in CAPTCHA_MARKERS)


# ============================================================
# WEB SEARCH: SEARXNG, DUCKDUCKGO, BING, GOOGLE, BRAVE
# ============================================================

class WebSearchTool(WebAITool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Искать информацию через несколько поисковых систем, переходя к следующей при ошибке."

    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    def _search_searxng(self, base_url: str, query: str, max_results: int) -> list[dict[str, str]]:
        base_url = _validate_public_url(base_url)
        response = _request_get(
            base_url + "/search",
            params={"q": query, "format": "json", "language": "ru-RU", "safesearch": 1},
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        if 300 <= response.status_code < 400:
            raise RuntimeError(f"SearXNG вернул редирект HTTP {response.status_code}; этот адрес пропущен.")
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as error:
            preview = " ".join(response.text[:180].split())
            raise RuntimeError(f"Вместо JSON получен другой ответ: {preview!r}") from error
        if not isinstance(data, dict) or not isinstance(data.get("results", []), list):
            raise RuntimeError("Некорректный формат ответа SearXNG.")

        results = []
        for item in data.get("results", []):
            if not isinstance(item, dict):
                continue
            result = _clean_result(item.get("title"), item.get("url"), item.get("content") or item.get("snippet"))
            if result:
                results.append(result)
            if len(results) >= max_results:
                break
        if not results:
            raise RuntimeError("SearXNG не вернул подходящих результатов.")
        return results

    def _search_html(self, engine: str, query: str, max_results: int) -> list[dict[str, str]]:
        engines = {
            "DuckDuckGo": ("https://html.duckduckgo.com/html/", {"q": query}),
            "Bing": ("https://www.bing.com/search", {"q": query}),
            "Google": ("https://www.google.com/search", {"q": query, "num": max_results}),
            "Brave": ("https://search.brave.com/search", {"q": query}),
        }
        url, params = engines[engine]
        response = _request_get(
            url,
            params=params,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
        )
        if 300 <= response.status_code < 400:
            raise RuntimeError(f"Редирект HTTP {response.status_code}; источник пропущен.")
        response.raise_for_status()
        page_html = response.text
        if _detect_captcha("", page_html, response.url):
            raise CaptchaDetectedError(f"{engine} может требовать ручную проверку.")

        parser = _SearchHTMLParser()
        parser.feed(page_html)
        results = []
        seen_urls = set()

        for item in parser.results:
            raw_url = item["url"].strip()
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            if parsed.netloc.lower().endswith("duckduckgo.com"):
                targets = query_params.get("uddg")
                if targets:
                    raw_url = unquote(targets[0])
            if parsed.path == "/url" and parsed.netloc.lower().endswith("google.com"):
                targets = query_params.get("q")
                if targets:
                    raw_url = targets[0]

            result = _clean_result(item.get("title"), raw_url, item.get("snippet", ""))
            if not result or result["url"] in seen_urls:
                continue
            seen_urls.add(result["url"])
            results.append(result)
            if len(results) >= max_results:
                break

        if not results:
            raise RuntimeError("Не удалось извлечь результаты из HTML; разметка могла измениться.")
        return results

    def _search_brave_api(self, query: str, max_results: int) -> list[dict[str, str]]:
        if not BRAVE_SEARCH_API_KEY:
            raise RuntimeError("Не задан BRAVE_SEARCH_API_KEY.")
        response = _request_get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(max_results, 20)},
            headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_SEARCH_API_KEY},
        )
        if 300 <= response.status_code < 400:
            raise RuntimeError(f"Brave API вернул редирект HTTP {response.status_code}.")
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            result = _clean_result(item.get("title"), item.get("url"), item.get("description"))
            if result:
                results.append(result)
            if len(results) >= max_results:
                break
        if not results:
            raise RuntimeError("Brave API не вернул результатов.")
        return results

    def _search_google_api(self, query: str, max_results: int) -> list[dict[str, str]]:
        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            raise RuntimeError("Не заданы GOOGLE_SEARCH_API_KEY и GOOGLE_SEARCH_ENGINE_ID.")
        response = _request_get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_SEARCH_ENGINE_ID, "q": query, "num": min(max_results, 10), "hl": "ru"},
        )
        if 300 <= response.status_code < 400:
            raise RuntimeError(f"Google API вернул редирект HTTP {response.status_code}.")
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("items", []):
            result = _clean_result(item.get("title"), item.get("link"), item.get("snippet"))
            if result:
                results.append(result)
            if len(results) >= max_results:
                break
        if not results:
            raise RuntimeError("Google API не вернул результатов.")
        return results

    def execute(self, query: str, max_results: int = 5, **kwargs: Any) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Поисковый запрос не должен быть пустым.")
        query = query.strip()
        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            max_results = 5
        max_results = max(1, min(max_results, 10))

        providers: list[tuple[str, Any]] = []
        if BRAVE_SEARCH_API_KEY:
            providers.append(("Brave Search API", lambda: self._search_brave_api(query, max_results)))
        if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
            providers.append(("Google Custom Search API", lambda: self._search_google_api(query, max_results)))

        # partial сохраняет аргументы каждого провайдера отдельно и не создаёт
        # замыканий с переменными цикла (instance/engine).
        for instance in SEARXNG_INSTANCES:
            providers.append(
                (
                    instance,
                    partial(self._search_searxng, instance, query, max_results),
                )
            )

        for engine in ("DuckDuckGo", "Bing", "Google", "Brave"):
            providers.append(
                (
                    engine,
                    partial(self._search_html, engine, query, max_results),
                )
            )

        failures = []
        for attempt, (source, search_function) in enumerate(providers, start=1):
            try:
                results = search_function()
                return {"query": query, "results": results, "source": source, "attempts": attempt, "failures": failures}
            except Exception as error:
                failures.append(f"{source}: {type(error).__name__}: {error}")

        raise RuntimeError("Не удалось выполнить поиск ни через один источник.\n" + "\n".join(f"- {failure}" for failure in failures))


# ============================================================
# OPEN A SEARCH IN MICROSOFT EDGE
# ============================================================

class EdgeSearchTool(WebAITool):
    @property
    def name(self) -> str:
        return "edge_search"

    @property
    def description(self) -> str:
        return "Открыть поисковый запрос в Microsoft Edge через выбранную поисковую систему."

    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "engine": {
                    "type": "string",
                    "enum": ["bing", "google", "brave", "duckduckgo"],
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    def execute(self, query: str, engine: str = "bing") -> dict[str, str]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Поисковый запрос не должен быть пустым.")
        engines = {
            "bing": "https://www.bing.com/search?q=",
            "google": "https://www.google.com/search?q=",
            "brave": "https://search.brave.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q=",
        }
        engine = engine.lower().strip()
        if engine not in engines:
            raise ValueError(f"Неизвестный поисковик: {engine}")
        url = engines[engine] + quote_plus(query.strip())
        _validate_public_url(url)
        if sys.platform != "win32":
            raise RuntimeError("Открытие Microsoft Edge поддерживается этим инструментом только в Windows.")
        try:
            subprocess.Popen(["msedge", url])
        except OSError:
            # Запасной вариант для Windows, если msedge не доступен как команда.
            subprocess.Popen(["cmd", "/c", "start", "", "msedge", url], shell=False)
        return {"status": "opened", "engine": engine, "url": url}


# ============================================================
# PLAYWRIGHT BROWSER
# ============================================================

class BrowserManager:
    """Persistent Chromium profile with URL checks and manual CAPTCHA handling."""

    def __init__(self):
        self._playwright = None
        self._context = None
        self._page = None

    def _guard_browser_route(self, route, request):
        try:
            _validate_public_url(request.url)
        except (ValueError, TypeError):
            route.abort()
        else:
            route.continue_()

    def _ensure_open(self):
        if self._context is not None:
            try:
                if self._page and not self._page.is_closed():
                    return
            except Exception:
                pass
        self.close()
        BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE),
                headless=False,
                accept_downloads=False,
                args=["--disable-extensions"],
            )
            self._context.route("**/*", self._guard_browser_route)
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
            self._page.set_default_timeout(10000)
        except Exception:
            self.close()
            raise

    def _captcha_status(self) -> dict[str, Any]:
        try:
            title = self._page.title()
            text = self._page.locator("body").inner_text(timeout=2500)
            url = self._page.url
        except PlaywrightError:
            return {"captcha_detected": False, "manual_verification_required": False, "message": ""}
        detected = _detect_captcha(title, text, url)
        return {
            "captcha_detected": detected,
            "manual_verification_required": detected,
            "message": "Сайт требует проверки. Решите её вручную в открытом браузере, затем повторите действие." if detected else "",
        }

    def open(self, url: str, fallback_urls: list[str] | None = None) -> dict[str, Any]:
        candidates = [url]
        if fallback_urls:
            if not isinstance(fallback_urls, list):
                raise ValueError("fallback_urls должен быть списком URL.")
            candidates.extend(fallback_urls)

        safe_candidates = []
        seen = set()
        for candidate in candidates:
            safe_candidate = _validate_public_url(candidate)
            if safe_candidate not in seen:
                seen.add(safe_candidate)
                safe_candidates.append(safe_candidate)
        if not safe_candidates:
            raise ValueError("Не указаны URL для открытия.")

        self._ensure_open()
        errors = []
        for candidate in safe_candidates:
            try:
                response = self._page.goto(candidate, wait_until="domcontentloaded", timeout=20000)
                final_url = self._page.url
                _validate_public_url(final_url)
                status_code = response.status if response is not None else None
                captcha = self._captcha_status()
                if captcha.get("captcha_detected"):
                    return {"url": final_url, "title": self._page.title(), "status_code": status_code, "attempted_urls": safe_candidates, **captcha}
                if status_code is not None and status_code >= 400:
                    errors.append(f"{candidate}: HTTP {status_code}")
                    continue
                return {
                    "url": final_url,
                    "title": self._page.title(),
                    "status_code": status_code,
                    "attempted_urls": safe_candidates,
                    "fallback_used": candidate != safe_candidates[0],
                    "previous_errors": errors,
                    **captcha,
                }
            except (PlaywrightError, ValueError) as error:
                errors.append(f"{candidate}: {type(error).__name__}: {error}")
        raise RuntimeError("Не удалось открыть ни один URL.\n" + "\n".join(f"- {error}" for error in errors))

    def read(self, max_chars: int = 12000) -> dict[str, Any]:
        self._ensure_open()
        _validate_public_url(self._page.url)
        captcha = self._captcha_status()
        if captcha.get("captcha_detected"):
            return {"url": self._page.url, "title": self._page.title(), "text": "", **captcha}
        try:
            max_chars = int(max_chars)
        except (TypeError, ValueError):
            max_chars = 12000
        max_chars = max(500, min(max_chars, 20000))
        try:
            text = self._page.locator("body").inner_text()
        except PlaywrightError as error:
            raise RuntimeError(f"Не удалось прочитать страницу: {error}") from error
        return {"url": self._page.url, "title": self._page.title(), "text": text[:max_chars], **captcha}

    def type_text(self, selector: str, text: str) -> dict[str, str]:
        self._ensure_open()
        _validate_public_url(self._page.url)
        captcha = self._captcha_status()
        if captcha.get("captcha_detected"):
            raise CaptchaDetectedError(captcha["message"])
        if not isinstance(selector, str) or not selector.strip():
            raise ValueError("CSS-селектор не должен быть пустым.")
        if not isinstance(text, str):
            raise ValueError("Вводимый текст должен быть строкой.")
        if len(text) > 2000:
            raise ValueError("Слишком длинный текст для ввода.")
        try:
            self._page.locator(selector).first.fill(text)
        except PlaywrightError as error:
            raise RuntimeError(f"Не удалось ввести текст в {selector!r}: {error}") from error
        return {"status": "text_entered", "selector": selector}

    def click(self, selector: str) -> dict[str, str]:
        self._ensure_open()
        _validate_public_url(self._page.url)
        captcha = self._captcha_status()
        if captcha.get("captcha_detected"):
            raise CaptchaDetectedError(captcha["message"])
        if not isinstance(selector, str) or not selector.strip():
            raise ValueError("CSS-селектор не должен быть пустым.")
        try:
            self._page.locator(selector).first.click()
        except PlaywrightError as error:
            raise RuntimeError(f"Не удалось нажать {selector!r}: {error}") from error
        return {"status": "clicked", "selector": selector}

    def close(self):
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
        self._context = None
        self._playwright = None
        self._page = None


# ============================================================
# BROWSER TOOL WRAPPERS
# ============================================================

class BrowserOpenTool(WebAITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_open"

    @property
    def description(self) -> str:
        return "Открыть публичный URL с резервными адресами и обнаружением CAPTCHA."

    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "fallback_urls": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["url"],
            "additionalProperties": False,
        }

    def execute(self, url: str, fallback_urls: list[str] | None = None) -> dict[str, Any]:
        return self.browser.open(url, fallback_urls=fallback_urls)


class BrowserReadTool(WebAITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_read"

    @property
    def description(self) -> str:
        return "Прочитать текст текущей страницы."

    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"max_chars": {"type": "integer", "minimum": 500, "maximum": 20000}},
            "additionalProperties": False,
        }

    def execute(self, max_chars: int = 12000) -> dict[str, Any]:
        return self.browser.read(max_chars)


class BrowserTypeTool(WebAITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_type"

    @property
    def description(self) -> str:
        return "Ввести текст в поле страницы по CSS-селектору."

    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"selector": {"type": "string"}, "text": {"type": "string"}},
            "required": ["selector", "text"],
            "additionalProperties": False,
        }

    def execute(self, selector: str, text: str) -> dict[str, str]:
        return self.browser.type_text(selector, text)


class BrowserClickTool(WebAITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_click"

    @property
    def description(self) -> str:
        return "Нажать элемент страницы по CSS-селектору."

    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": ["selector"],
            "additionalProperties": False,
        }

    def execute(self, selector: str) -> dict[str, str]:
        return self.browser.click(selector)
