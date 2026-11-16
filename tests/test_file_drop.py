"""Tests for recoverable file drop handling."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.ui.python.file_drop import move_file_to_recycle_bin


def test_regular_file_is_sent_to_system_trash(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("hello", encoding="utf-8")
    send_to_trash = Mock()
    fake_module = SimpleNamespace(send2trash=send_to_trash)
    with patch.dict("sys.modules", {"send2trash": fake_module}):
        move_file_to_recycle_bin(source)
    send_to_trash.assert_called_once_with(str(source.resolve()))


def test_missing_file_is_rejected(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        move_file_to_recycle_bin(tmp_path / "missing.txt")


def test_directory_is_not_accepted(tmp_path: Path):
    with pytest.raises(ValueError, match="только отдельные файлы"):
        move_file_to_recycle_bin(tmp_path)
