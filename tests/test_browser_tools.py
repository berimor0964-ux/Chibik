
from app.ai.web_tools import WebSearchTool

tool = WebSearchTool()

try:
    result = tool.execute(
        query="официальная документация Python",
        max_results=5,
    )

    print("Источник поиска:", result["source"])
    print("Количество попыток:", result["attempts"])
    print()

    for index, item in enumerate(result["results"], start=1):
        print(f"{index}. {item['title']}")
        print("URL:", item["url"])
        print("Описание:", item["snippet"])
        print()

except Exception as error:
    print("ПОИСК НЕ УДАЛСЯ:")
    print(error)
