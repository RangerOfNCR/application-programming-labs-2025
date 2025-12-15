from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd


def plot_values(df: pd.DataFrame, column: str, output_file: str) -> None:
    """
    Строит график значений по отсортированным данным.
    x — индекс в списке
    y — значение выбранной величины
    """
    plt.figure(figsize=(12, 6))
    plt.plot(df[column])

    plt.title(f"График значений колонки '{column}'")
    plt.xlabel("Номер аудиофайла (после сортировки)")
    plt.ylabel(column)

    plt.grid(True)

    plt.savefig(output_file)
    plt.close()
