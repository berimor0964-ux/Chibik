#tools.py
from __future__ import annotations

from abc import ABC, abstractmethod
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
import ipaddress
import os
import socket
import subprocess
import sys

import requests
from playwright.sync_api import sync_playwright, Error as PlaywrightError


# ============================================================
# НАСТРОЙКИ
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BROWSER_PROFILE = PROJECT_ROOT / "data" / "browser_profile"

# Можно изменить список через переменную окружения:
# SEARXNG_INSTANCES=https://searx.be,https://searx.tiekoetter.com
DEFAULT_SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://search.sapti.me",
    "https://searx.ononoki.org",
    "https://priv.au",
    "https://opnxng.com",
]

SEARXNG_INSTANCES = [
    url.strip().rstrip("/")
    for url in os.getenv(
        "SEARXNG_INSTANCES",
        ",".join(DEFAULT_SEARXNG_INSTANCES),
    ).split(",")
    if url.strip()
]

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 12

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# ============================================================
# БАЗОВЫЙ ИНТЕРФЕЙС ИНСТРУМЕНТОВ
# ============================================================

class AITool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    def parameters_schema(self) -> dict:
        schemas = {
            "find_object": {
                "type": "object",
                "properties": {
                    "object_type": {"type": "string"},
                },
                "required": ["object_type"],
                "additionalProperties": False,
            },
            "move_to": {
                "type": "object",
                "properties": {
                    "start": {"type": "object"},
                    "target": {"type": "object"},
                },
                "required": ["start", "target"],
                "additionalProperties": False,
            },
            "build_object": {
                "type": "object",
                "properties": {
                    "object_type": {"type": "string"},
                    "position": {"type": "object"},
                },
                "required": ["object_type", "position"],
                "additionalProperties": False,
            },
            "talk_to_character": {
                "type": "object",
                "properties": {
                    "character_id": {"type": "string"},
                },
                "required": ["character_id"],
                "additionalProperties": False,
            },
            "web_search": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
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
                "properties": {
                    "max_chars": {"type": "integer"},
                },
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
                "properties": {
                    "selector": {"type": "string"},
                },
                "required": ["selector"],
                "additionalProperties": False,
            },
        }

        return schemas.get(
            self.name,
            {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        )

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema(),
            },
        }


# ============================================================
# ИНСТРУМЕНТЫ ВИРТУАЛЬНОГО МИРА
# ============================================================

class FindObjectTool(AITool):
    @property
    def name(self) -> str:
        return "find_object"

    @property
    def description(self) -> str:
        return "Найти объект в виртуальном мире."

    def execute(self, world, object_type: str) -> Any:
        return world.find_object(object_type)


class MoveToTool(AITool):
    @property
    def name(self) -> str:
        return "move_to"

    @property
    def description(self) -> str:
        return "Найти путь от начальной позиции к целевой."

    def execute(self, world, start, target) -> Any:
        return world.find_path(start, target)


class BuildObjectTool(AITool):
    @property
    def name(self) -> str:
        return "build_object"

    @property
    def description(self) -> str:
        return "Создать объект в виртуальном мире."

    def execute(self, world, object_type: str, position) -> Any:
        if not world.can_build(object_type, position):
            return None
        return world.spawn_object(object_type, position)


class TalkToCharacterTool(AITool):
    @property
    def name(self) -> str:
        return "talk_to_character"

    @property
    def description(self) -> str:
        return "Начать взаимодействие с другим персонажем."

    def execute(self, character_id: str) -> dict[str, str]:
        return {
            "character_id": character_id,
            "status": "requested",
        }


# ============================================================
# РЕЕСТР ИНСТРУМЕНТОВ
# ============================================================

class AIToolRegistry:
    def __init__(self):
        self._tools: dict[str, AITool] = {}

    def register(self, tool: AITool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AITool | None:
        return self._tools.get(name)

    def get_all(self) -> list[AITool]:
        return list(self._tools.values())

    def execute(self, name: str, **kwargs: Any) -> Any:
        tool = self.get(name)

        if tool is None:
            raise ValueError(f"AI tool not found: {name}")

        return tool.execute(**kwargs)


# ============================================================
# ПРОВЕРКА URL И ЗАЩИТА ОТ SSRF
# ============================================================

def _validate_public_url(url: str) -> str:
    """Разрешает HTTP(S), блокируя localhost и непубличные IP."""

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

    if (
        host == "localhost"
        or host.endswith(".localhost")
        or host == "localhost.localdomain"
    ):
        raise ValueError("Доступ к localhost запрещён.")

    port = port or (443 if scheme == "https" else 80)

    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            )
            addresses = list({
                ipaddress.ip_address(record[4][0])
                for record in records
            })
        except (socket.gaierror, OSError, ValueError) as error:
            raise ValueError(
                f"Не удалось разрешить имя хоста {host!r}."
            ) from error

    if not addresses:
        raise ValueError("Не найден IP-адрес хоста.")

    if any(not address.is_global for address in addresses):
        raise ValueError(
            "Доступ к локальным или непубличным IP запрещён."
        )

    return url


def _safe_result_url(url: str) -> str | None:
    try:
        return _validate_public_url(url)
    except (ValueError, TypeError):
        return None


# ============================================================
# HTML-ПАРСЕР ПОИСКОВОЙ ВЫДАЧИ
# ============================================================

class _SearchHTMLParser(HTMLParser):
    """Извлекает заголовки и ссылки из HTML DuckDuckGo."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self.current_result: dict[str, str] | None = None
        self.capture_title = False
        self.title_container_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())

        if tag in ("h2", "h3") and classes.intersection({
            "result-title",
            "result__title",
        }):
            self.title_container_depth += 1

        is_result_link = (
            tag == "a"
            and bool(classes.intersection({
                "result__a",
                "result-link",
                "result__title",
            }))
        )

        is_link_inside_title = (
            tag == "a" and self.title_container_depth > 0
        )

        if (is_result_link or is_link_inside_title) and attrs.get("href"):
            self.current_result = {
                "title": "",
                "url": attrs["href"],
                "snippet": "",
            }
            self.capture_title = True

    def handle_data(self, data):
        if self.capture_title and self.current_result is not None:
            self.current_result["title"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.capture_title:
            if self.current_result is not None:
                title = " ".join(
                    self.current_result["title"].split()
                )
                url = self.current_result["url"].strip()

                if title and url:
                    self.results.append({
                        "title": title,
                        "url": url,
                        "snippet": self.current_result.get("snippet", ""),
                    })

            self.current_result = None
            self.capture_title = False

        elif tag in ("h2", "h3") and self.title_container_depth > 0:
            self.title_container_depth -= 1


# ============================================================
# ПОИСК: НЕСКОЛЬКО ИСТОЧНИКОВ И АВТОМАТИЧЕСКИЙ ПЕРЕБОР
# ============================================================

class WebSearchTool(AITool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Искать информацию через несколько поисковых источников. "
            "При сбое одного источника автоматически пробует следующий."
        )

    def _search_searxng(
        self,
        base_url: str,
        query: str,
        max_results: int,
    ) -> list[dict[str, str]]:
        base_url = _validate_public_url(base_url)

        response = requests.get(
            base_url + "/search",
            params={
                "q": query,
                "format": "json",
                "language": "ru-RU",
                "safesearch": 1,
            },
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=False,
        )

        if 300 <= response.status_code < 400:
            raise RuntimeError(
                f"сервер перенаправил запрос: HTTP {response.status_code}"
            )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as error:
            content_type = response.headers.get("Content-Type", "")
            preview = " ".join(response.text[:180].split())

            raise RuntimeError(
                f"вместо JSON получен другой ответ; "
                f"Content-Type={content_type!r}; "
                f"начало ответа={preview!r}"
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError("сервер вернул неожиданный формат JSON")

        raw_results = data.get("results", [])

        if not isinstance(raw_results, list):
            raise RuntimeError("поле results имеет неверный формат")

        results = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or "").strip()
            raw_url = str(item.get("url") or "").strip()
            snippet = str(
                item.get("content") or item.get("snippet") or ""
            ).strip()

            safe_url = _safe_result_url(raw_url)

            if not title or not safe_url:
                continue

            results.append({
                "title": title[:500],
                "url": safe_url,
                "snippet": snippet[:1200],
            })

            if len(results) >= max_results:
                break

        if not results:
            raise RuntimeError("подходящих результатов нет")

        return results

    def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
    ) -> list[dict[str, str]]:
        response = requests.get(
            _validate_public_url(
                "https://html.duckduckgo.com/html/"
            ),
            params={"q": query},
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=False,
        )

        response.raise_for_status()

        parser = _SearchHTMLParser()
        parser.feed(response.text)

        results = []
        seen_urls = set()

        for item in parser.results:
            raw_url = item["url"].strip()
            parsed = urlparse(raw_url)

            # Некоторые ссылки DuckDuckGo содержат целевой адрес в uddg.
            targets = parse_qs(parsed.query).get("uddg")
            if targets:
                raw_url = targets[0]

            safe_url = _safe_result_url(raw_url)
            title = item["title"].strip()

            if not title or not safe_url or safe_url in seen_urls:
                continue

            seen_urls.add(safe_url)

            results.append({
                "title": title[:500],
                "url": safe_url,
                "snippet": item.get("snippet", "")[:1200],
            })

            if len(results) >= max_results:
                break

        if not results:
            preview = " ".join(response.text[:250].split())
            lowered = response.text.lower()

            if any(word in lowered for word in (
                "captcha",
                "challenge",
                "verify you are human",
            )):
                reason = "получена CAPTCHA или проверка браузера"
            else:
                reason = (
                    "парсер не нашёл результатов в HTML; "
                    f"начало ответа: {preview!r}"
                )

            raise RuntimeError(reason)

        return results

    def execute(
        self,
        query: str,
        max_results: int = 5,
        **kwargs: Any,
    ) -> dict:
        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Поисковый запрос должен быть непустой строкой."
            )

        query = query.strip()

        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            max_results = 5

        max_results = max(1, min(max_results, 10))

        failures: list[str] = []
        attempted = 0

        # Сначала пробуем все настроенные экземпляры SearXNG.
        for instance in SEARXNG_INSTANCES:
            attempted += 1

            try:
                results = self._search_searxng(
                    instance,
                    query,
                    max_results,
                )

                return {
                    "query": query,
                    "results": results,
                    "source": instance,
                    "attempts": attempted,
                    "failures": failures,
                }

            except Exception as error:
                failures.append(
                    f"{instance}: {type(error).__name__}: {error}"
                )

        # Затем пробуем DuckDuckGo.
        attempted += 1

        try:
            results = self._search_duckduckgo(
                query,
                max_results,
            )

            return {
                "query": query,
                "results": results,
                "source": "DuckDuckGo HTML",
                "attempts": attempted,
                "failures": failures,
            }

        except Exception as error:
            failures.append(
                f"DuckDuckGo: {type(error).__name__}: {error}"
            )

        raise RuntimeError(
            "Не удалось выполнить поиск ни через один источник.\n"
            + "\n".join(f"- {error}" for error in failures)
        )


# ============================================================
# БРАУЗЕР PLAYWRIGHT
# ============================================================

class BrowserManager:
    """Постоянный профиль Chromium с проверкой URL."""

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
            self._context = (
                self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(BROWSER_PROFILE),
                    headless=False,
                    accept_downloads=False,
                    args=["--disable-extensions"],
                )
            )

            self._context.route(
                "**/*",
                self._guard_browser_route,
            )

            self._page = (
                self._context.pages[0]
                if self._context.pages
                else self._context.new_page()
            )

            self._page.set_default_timeout(10000)

        except Exception:
            self.close()
            raise

    def open(
        self,
        url: str,
        fallback_urls: list[str] | None = None,
    ) -> dict:
        """
        Пробует открыть основной URL, затем альтернативные URL по очереди.

        fallback_urls необходимо передавать явно. Автоматически угадать
        правильный альтернативный адрес любого сайта невозможно.
        """
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

        self._ensure_open()
        errors = []

        for candidate in safe_candidates:
            try:
                response = self._page.goto(
                    candidate,
                    wait_until="domcontentloaded",
                    timeout=20000,
                )

                final_url = self._page.url
                _validate_public_url(final_url)

                status_code = (
                    response.status if response is not None else None
                )

                if status_code is not None and status_code >= 400:
                    errors.append(
                        f"{candidate}: HTTP {status_code}"
                    )
                    continue

                return {
                    "url": final_url,
                    "title": self._page.title(),
                    "status_code": status_code,
                    "attempted_urls": safe_candidates,
                    "fallback_used": candidate != safe_candidates[0],
                    "previous_errors": errors,
                }

            except (PlaywrightError, ValueError) as error:
                errors.append(
                    f"{candidate}: {type(error).__name__}: {error}"
                )

        raise RuntimeError(
            "Не удалось открыть ни один URL.\n"
            + "\n".join(f"- {error}" for error in errors)
        )

    def read(self, max_chars: int = 12000) -> dict:
        self._ensure_open()
        _validate_public_url(self._page.url)

        try:
            max_chars = int(max_chars)
        except (TypeError, ValueError):
            max_chars = 12000

        max_chars = max(500, min(max_chars, 20000))

        try:
            text = self._page.locator("body").inner_text()
        except PlaywrightError as error:
            raise RuntimeError(
                f"Не удалось прочитать страницу: {error}"
            ) from error

        return {
            "url": self._page.url,
            "title": self._page.title(),
            "text": text[:max_chars],
        }

    def type_text(self, selector: str, text: str) -> dict:
        self._ensure_open()
        _validate_public_url(self._page.url)

        if not isinstance(selector, str) or not selector.strip():
            raise ValueError("CSS-селектор не должен быть пустым.")

        if not isinstance(text, str):
            raise ValueError("Вводимый текст должен быть строкой.")

        if len(text) > 2000:
            raise ValueError("Слишком длинный текст для ввода.")

        try:
            self._page.locator(selector).first.fill(text)
        except PlaywrightError as error:
            raise RuntimeError(
                f"Не удалось ввести текст в {selector!r}: {error}"
            ) from error

        return {
            "status": "text_entered",
            "selector": selector,
        }

    def click(self, selector: str) -> dict:
        self._ensure_open()
        _validate_public_url(self._page.url)

        if not isinstance(selector, str) or not selector.strip():
            raise ValueError("CSS-селектор не должен быть пустым.")

        try:
            self._page.locator(selector).first.click()
        except PlaywrightError as error:
            raise RuntimeError(
                f"Не удалось нажать {selector!r}: {error}"
            ) from error

        return {
            "status": "clicked",
            "selector": selector,
        }

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
# ОБЁРТКИ БРАУЗЕРНЫХ ИНСТРУМЕНТОВ
# ============================================================

class BrowserOpenTool(AITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_open"

    @property
    def description(self) -> str:
        return "Открыть публичный URL с возможностью попробовать резервные адреса."

    def execute(
        self,
        url: str,
        fallback_urls: list[str] | None = None,
    ) -> dict:
        return self.browser.open(
            url,
            fallback_urls=fallback_urls,
        )


class BrowserReadTool(AITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_read"

    @property
    def description(self) -> str:
        return "Прочитать текст текущей открытой страницы."

    def execute(self, max_chars: int = 12000) -> dict:
        return self.browser.read(max_chars)


class BrowserTypeTool(AITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_type"

    @property
    def description(self) -> str:
        return "Ввести текст в поле страницы по CSS-селектору."

    def execute(self, selector: str, text: str) -> dict:
        return self.browser.type_text(selector, text)


class BrowserClickTool(AITool):
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @property
    def name(self) -> str:
        return "browser_click"

    @property
    def description(self) -> str:
        return "Нажать элемент страницы по CSS-селектору."

    def execute(self, selector: str) -> dict:
        return self.browser.click(selector)
