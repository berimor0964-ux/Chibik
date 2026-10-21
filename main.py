import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def main():
    app = QGuiApplication(sys.argv)

    project_root = Path(__file__).parent.resolve()
    assets_path = project_root / "assets"
    qml_dir = project_root / "app" / "ui" / "qml"

    engine = QQmlApplicationEngine()

    engine.rootContext().setContextProperty(
        "assetsPath",
        assets_path.as_posix()
    )

    engine.addImportPath(str(qml_dir))
    engine.load(str(qml_dir / "Main.qml"))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()