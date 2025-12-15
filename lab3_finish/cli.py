"""
Модуль для обработки аргументов командной строки.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CliArgs:
    input: Path
    output: Path


def parse_args() -> CliArgs:
    """
    Парсинг аргументов командной строки.

    :return: CliArgs объект.
    """
    parser = argparse.ArgumentParser(description="Reverse audio using NumPy + SoundFile")
    parser.add_argument("--input", required=True, help="Путь к исходному аудиофайлу")
    parser.add_argument("--output", required=True, help="Куда сохранить перевёрнутый файл")

    args = parser.parse_args()
    return CliArgs(input=Path(args.input), output=Path(args.output))
