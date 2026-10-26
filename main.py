import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication, QFontDatabase
from PySide6.QtQml import QQmlApplicationEngine


def main():
    print("1. Старт приложения...")
    app = QGuiApplication(sys.argv)

    project_root = Path(__file__).parent.resolve()
    assets_path = project_root / "assets"
    qml_dir = project_root / "app" / "ui" / "qml"

    # Загрузка шрифта
    font_path = assets_path / "fonts" / "Minecraft.ttf"
    print(f"2. Ищу шрифт: {font_path}")

    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id == -1:
            print("⚠️ Шрифт не загружен (файл есть, но Qt его не понял)")
        else:
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"Шрифт загружен: {families}")
    else:
        print("Файл шрифта НЕ НАЙДЕН по этому пути!")

    print("3. Создаю движок QML...")
    engine = QQmlApplicationEngine()

    engine.rootContext().setContextProperty(
        "assetsPath",
        assets_path.as_posix()
    )

    engine.addImportPath(str(qml_dir))

    print("4. Загружаю Main.qml...")
    engine.load(str(qml_dir / "Main.qml"))

    if not engine.rootObjects():
        print("ОШИБКА: QML не загрузился (файл не найден или в нем ошибка)!")
        sys.exit(-1)

    print("5. Запуск окна...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()