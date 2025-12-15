"""
Модуль для построения графиков аудио.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional


class AudioPlotter:
    """Класс для визуализации аудиосигналов."""

    def plot(self, original: np.ndarray, reversed_audio: np.ndarray) -> None:
        """
        Строит графики исходного и перевёрнутого сигнала.

        :param original: Исходный аудиосигнал.
        :param reversed_audio: Перевёрнутый аудиосигнал.
        """
        plt.figure(figsize=(12, 6))

        plt.subplot(2, 1, 1)
        plt.title("Исходное аудио")
        plt.plot(original)
        plt.xlabel("Сэмплы")

        plt.subplot(2, 1, 2)
        plt.title("Перевернутое аудио")
        plt.plot(reversed_audio)
        plt.xlabel("Сэмплы")

        plt.tight_layout()
        plt.show()
