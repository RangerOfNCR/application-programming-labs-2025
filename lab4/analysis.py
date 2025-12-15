import pandas as pd
from typing import Optional


def sort_by_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Сортировка DataFrame по указанной колонке."""
    return df.sort_values(by=column).reset_index(drop=True)


def filter_by_column(
    df: pd.DataFrame,
    column: str,
    min_value: Optional[float],
    max_value: Optional[float]
) -> pd.DataFrame:
    """Фильтрация DataFrame по диапазону значений."""
    if min_value is not None:
        df = df[df[column] >= min_value]
    if max_value is not None:
        df = df[df[column] <= max_value]
    return df.reset_index(drop=True)
