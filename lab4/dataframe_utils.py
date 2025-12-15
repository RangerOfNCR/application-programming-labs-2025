import csv
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


def load_annotation(csv_file: Path) -> pd.DataFrame:
    """
    Загружает CSV аннотацию и формирует DataFrame.
    Должны быть колонки 'absolute_path' и 'relative_path'.
    """
    data: List[dict] = []

    with csv_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "absolute_path": row["absolute_path"],
                "relative_path": row["relative_path"],
            })

    df = pd.DataFrame(data)
    return df


def read_audio_waveform(path: Path) -> np.ndarray:
    """
    Читает WAV файл вручную с помощью numpy.
    Поддержка MP3 отсутствует (по условиям лабораторной без pydub).
    """
    import wave

    with wave.open(str(path), "rb") as wav:
        frames = wav.readframes(wav.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16)

    return samples


def add_max_amplitude_column(df: pd.DataFrame, sounds_dir: Path) -> pd.DataFrame:
    amplitudes = []

    for rel_path in df["relative_path"]:
        rel = Path(rel_path)

        # Если путь в CSV начинается со "sounds", удаляем этот сегмент
        if rel.parts and rel.parts[0].lower() == "sounds":
            rel = Path(*rel.parts[1:])

        audio_path = sounds_dir / rel

        samples = read_audio_waveform(audio_path)
        amplitudes.append(float(np.max(np.abs(samples))))

    df["max_amplitude"] = amplitudes
    return df

