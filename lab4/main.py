import argparse
from pathlib import Path

from dataframe_utils import load_annotation, add_max_amplitude_column
from analysis import sort_by_column, filter_by_column
from plot import plot_values


def parse_args() -> argparse.Namespace:
    """Парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(description="Лабораторная №3 — работа с аудио и DataFrame.")
    parser.add_argument("--csv", type=str, required=True, help="Имя CSV файла аннотации.")
    parser.add_argument("--sounds", type=str, default="sounds", help="Папка со звуками.")
    parser.add_argument("--sort", type=str, default="max_amplitude", help="Колонка для сортировки.")
    parser.add_argument("--filter-min", type=float, default=None, help="Минимальное значение для фильтрации.")
    parser.add_argument("--filter-max", type=float, default=None, help="Максимальное значение для фильтрации.")
    return parser.parse_args()


def main() -> None:
    """Главная функция программы."""
    try:
        args = parse_args()
        csv_path = Path(args.csv)
        sounds_dir = Path(args.sounds)

        df = load_annotation(csv_path)

        df = add_max_amplitude_column(df, sounds_dir)

        df_sorted = sort_by_column(df, args.sort)

        if args.filter_min is not None or args.filter_max is not None:
            df_sorted = filter_by_column(
                df_sorted,
                args.sort,
                args.filter_min,
                args.filter_max
            )

        plot_values(
            df_sorted,
            column=args.sort,
            output_file="amplitude_plot.png"
        )

        df_sorted.to_csv("result.csv", index=False)
        print("✔ Готово! Данные сохранены в result.csv, график — amplitude_plot.png.")

    except Exception as exc:
        print(f"Ошибка: {exc}")


if __name__ == "__main__":
    main()
