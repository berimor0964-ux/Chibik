"""Единая точка входа Chibik Desktop Pet (PySide6/QML)."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

from app.core.event_bus import EventBus
from app.ui.python.bridge import UiBridge


def main() -> int:
    """Запускает прозрачное окно Миры поверх рабочего стола."""
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Chibik")

    project_root = Path(__file__).resolve().parent.parent
    assets_path = project_root / "assets"
    qml_dir = project_root / "app" / "ui" / "qml"
    main_qml = qml_dir / "Main.qml"

    if not main_qml.is_file():
        raise FileNotFoundError(f"Не найден главный QML-файл: {main_qml}")

    font_path = assets_path / "fonts" / "Minecraft.ttf"
    if font_path.is_file():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id == -1:
            print(f"Предупреждение: не удалось загрузить шрифт {font_path}")

    engine = QQmlApplicationEngine()

    def report_qml_warnings(warnings):
        for warning in warnings:
            print(f"QML: {warning.toString()}", file=sys.stderr)

    engine.warnings.connect(report_qml_warnings)

    bridge = UiBridge(EventBus())

    engine.rootContext().setContextProperty(
        "assetsUrl",
        QUrl.fromLocalFile(str(assets_path)).toString().rstrip("/")
    )
    engine.rootContext().setContextProperty("assetsPath",
                                            assets_path.as_posix())
    engine.rootContext().setContextProperty("houseX",
                                            bridge.controller.geometry.x())
    engine.rootContext().setContextProperty("houseY",
                                            bridge.controller.geometry.y())
    engine.rootContext().setContextProperty("houseWidth",
                                            bridge.controller.geometry.width())
    engine.rootContext().setContextProperty("houseHeight",
                                            bridge.controller.geometry.height())
    engine.rootContext().setContextProperty("bridge", bridge)

    engine.addImportPath(str(qml_dir))
    engine.load(str(main_qml))

    if not engine.rootObjects():
        bridge.close()
        print(f"Не удалось загрузить интерфейс: {main_qml}", file=sys.stderr)
        return 1

    app.aboutToQuit.connect(bridge.close)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())