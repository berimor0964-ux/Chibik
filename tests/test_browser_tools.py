
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.tools import (
    WebSearchTool,
    BrowserManager,
)


def main():
    query = input("Что ищем? ").strip()

    search = WebSearchTool()
    results = search.execute(query=query)

    for index, result in enumerate(results["results"], start=1):
        print(f"\n{index}. {result['title']}")
        print(result["url"])
        print(result["snippet"])

    if not results["results"]:
        print("Поиск не вернул результатов.")
        return

    browser = BrowserManager()

    try:
        choice = input(
            "\nВведи номер результата для открытия "
            "(Enter — пропустить): "
        ).strip()

        if not choice:
            return

        index = int(choice) - 1
        if index < 0 or index >= len(results["results"]):
            print("Неверный номер.")
            return

        opened = browser.open(results["results"][index]["url"])
        print("\nОткрыта страница:", opened["title"])

        page = browser.read()
        print("\nТекст страницы:\n")
        print(page["text"])

        input("\nНажми Enter, чтобы закрыть браузер...")

    finally:
        browser.close()


if __name__ == "__main__":
    main()
