#!/usr/bin/env python3
"""
Основной модуль для скачивания WAV файлов с MixKit.
"""

import argparse
from pathlib import Path
import sys

from scraper import MixKitScraper
from iterator import AudioPathIterator


def parse_arguments() -> argparse.Namespace:
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description='Скачивание WAV файлов с сайта MixKit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Примеры использования:
  python main.py --count 50 --save_dir wav_sounds --annotation wav_annotation.csv
  python main.py --min_duration 5 --count 100 --save_dir audio_wav --annotation data.csv --pages 20
  python main.py --min_duration 10 --count 200 --save_dir sounds_wav --annotation all.csv --pages 30 --workers 1
        """
    )
    
    parser.add_argument(
        '--min_duration',
        type=int,
        default=5,
        help='Минимальная длительность WAV файлов в секундах (по умолчанию: 5)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        required=True,
        help='Количество WAV файлов для скачивания'
    )
    
    parser.add_argument(
        '--save_dir',
        type=str,
        required=True,
        help='Директория для сохранения WAV файлов'
    )
    
    parser.add_argument(
        '--annotation',
        type=str,
        required=True,
        help='Путь к файлу аннотации (CSV)'
    )
    
    parser.add_argument(
        '--pages',
        type=int,
        default=5,
        help='Количество страниц для парсинга (по умолчанию: 5)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Количество рабочих потоков (рекомендуется 1 для стабильности)'
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Проверяет валидность аргументов."""
    if args.count < 1:
        raise ValueError("Количество файлов должно быть положительным")
    
    if args.min_duration < 0:
        raise ValueError("Минимальная длительность не может быть отрицательной")
    
    if args.pages < 1:
        raise ValueError("Количество страниц должно быть положительным")
    
    if args.workers < 1:
        raise ValueError("Количество потоков должно быть положительным")
    
    print(f"[INFO] Будет скачано {args.count} WAV файлов")
    print(f"[INFO] Будут парситься {args.pages} страниц")


def main() -> None:
    """Основная функция программы."""
    try:
        args = parse_arguments()
        validate_arguments(args)
        
        scraper = MixKitScraper(workers=args.workers)
        
        downloaded_count = scraper.scrape_audio_files(
            min_duration=args.min_duration,
            max_files=args.count,
            save_dir=Path(args.save_dir),
            annotation_path=Path(args.annotation),
            num_pages=args.pages
        )
        
        print("\n" + "=" * 50)
        print(f"РЕЗУЛЬТАТ СКАЧИВАНИЯ WAV ФАЙЛОВ")
        print(f"Запрошено: {args.count}")
        print(f"Скачано: {downloaded_count}")
        print(f"Директория: {args.save_dir}")
        print(f"Аннотация: {args.annotation}")
        print("=" * 50)
        
        if downloaded_count > 0:
            print("\nПервые 5 файлов:")
            iterator = AudioPathIterator(args.annotation)
            
            for i, file_path in enumerate(iterator):
                if i >= 5:
                    break
                print(f"  {i+1}. {Path(file_path).name}")
            
            print(f"\nВсего WAV файлов: {len(iterator)}")
        else:
            print("\nНе скачано ни одного WAV файла.")
            
    except ValueError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана")
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()