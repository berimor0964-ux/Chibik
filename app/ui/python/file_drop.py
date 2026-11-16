"""Safe file drop handling for the desktop pet."""
from __future__ import annotations

from pathlib import Path


def move_file_to_recycle_bin(file_path: str | Path) -> None:
    """Move one regular local file to the OS recycle bin (never permanently unlink)."""
    path = Path(file_path).expanduser()
    if path.is_symlink():
        raise ValueError("Я не буду удалять символические ссылки.")
    if not path.exists():
        raise FileNotFoundError("Файл больше не существует.")
    if not path.is_file():
        raise ValueError("Мира принимает только отдельные файлы, не папки.")

    # send2trash uses the Windows Recycle Bin and equivalent desktop trash on other OSes.
    try:
        from send2trash import send2trash
    except ImportError as error:
        raise RuntimeError(
            "Не установлен обработчик Корзины. Выполни: "
            "python -m pip install send2trash"
        ) from error
    send2trash(str(path.resolve()))
