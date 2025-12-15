"""
Модуль для загрузки, обработки и сохранения аудио.
"""

from pathlib import Path
from typing import Tuple
import numpy as np
import soundfile as sf


class AudioProcessor:
    """Класс для работы с аудиофайлами: чтение, реверс, сохранение."""

    def read_audio(self, path: Path) -> Tuple[np.ndarray, int]:
        """
        Считывает аудио-файл.

        :param path: Путь к файлу.
        :return: Кортеж (аудиоданные, частота дискретизации).
        """
        try:
            audio, samplerate = sf.read(path)
            return audio, samplerate
        except Exception as exc:
            raise RuntimeError(f"Ошибка чтения аудио: {exc}")

    def reverse_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Переворачивает аудиосигнал.

        :param audio: Исходный массив NumPy.
        :return: Перевернутый массив.
        """
        return audio[::-1]

    def save_audio(self, path: Path, audio: np.ndarray, samplerate: int) -> None:
        """
        Сохраняет аудио в файл.

        :param path: Путь куда сохранить.
        :param audio: Аудиоданные.
        :param samplerate: Частота дискретизации.
        """
        try:
            sf.write(path, audio, samplerate)
        except Exception as exc:
            raise RuntimeError(f"Ошибка сохранения аудио: {exc}")
