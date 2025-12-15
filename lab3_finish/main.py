"""
Главный модуль: объединяет работу процессора, визуализатора и CLI.
"""

from pathlib import Path
from cli import parse_args
from audio_processor import AudioProcessor
from plotter import AudioPlotter


def main() -> None:
    """Главная логика программы."""
    args = parse_args()

    processor = AudioProcessor()
    plotter = AudioPlotter()

    # 1. Чтение аудио
    audio, sr = processor.read_audio(args.input)

    # Информация пользователю
    duration = audio.shape[0] / sr
    print(f"Формат: {audio.dtype}")
    print(f"Частота дискретизации: {sr} Гц")
    print(f"Длительность: {duration:.2f} секунд")

    # 2. Реверс аудио
    reversed_audio = processor.reverse_audio(audio)

    # 3. Построение графиков
    plotter.plot(audio, reversed_audio)

    # 4. Сохранить файл
    processor.save_audio(args.output, reversed_audio, sr)

    print(f"\nГотово! Перевернутый файл сохранён в: {args.output}")


if __name__ == "__main__":
    main()
