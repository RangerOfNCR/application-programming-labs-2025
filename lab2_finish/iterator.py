from pathlib import Path
import csv
from typing import Iterator, Union, List


class AudioPathIterator:
    """
    Итератор по путям к аудиофайлам.
    Поддерживает чтение из CSV-аннотации или директории с файлами.
    """
    
    def __init__(self, source: Union[str, Path]) -> None:
        """
        Инициализирует итератор.
        
        Args:
            source: Путь к CSV-файлу с аннотациями или директории с аудиофайлами.
            
        Raises:
            ValueError: Если source не является валидным CSV-файлом или директорией.
        """
        self._paths: List[str] = []
        self._index: int = 0
        self._load_paths(source)
    
    def _load_paths(self, source: Union[str, Path]) -> None:
        """Загружает пути к файлам из указанного источника."""
        source_path = Path(source)
        
        if source_path.is_file() and source_path.suffix.lower() == ".csv":
            self._load_from_csv(source_path)
        elif source_path.is_dir():
            self._load_from_directory(source_path)
        else:
            raise ValueError(
                "Источник должен быть либо CSV-файлом с аннотациями, "
                "либо директорией с аудиофайлами."
            )
    
    def _load_from_csv(self, csv_path: Path) -> None:
        """Загружает пути из CSV-файла с аннотациями."""
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                if 'absolute_path' not in reader.fieldnames:
                    raise ValueError("CSV файл должен содержать колонку 'absolute_path'")
                
                for row in reader:
                    if row['absolute_path']:
                        self._paths.append(row['absolute_path'])
        except Exception as e:
            raise ValueError(f"Ошибка чтения CSV файла: {e}")
    
    def _load_from_directory(self, directory: Path) -> None:
        """Загружает пути из директории с аудиофайлами."""
        audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
        try:
            for file_path in directory.rglob('*'):
                if file_path.suffix.lower() in audio_extensions:
                    self._paths.append(str(file_path.resolve()))
        except Exception as e:
            raise ValueError(f"Ошибка чтения директории: {e}")
    
    def __iter__(self) -> Iterator[str]:
        """Возвращает итератор."""
        self._index = 0
        return self
    
    def __next__(self) -> str:
        """Возвращает следующий путь к файлу."""
        if self._index >= len(self._paths):
            raise StopIteration
        path = self._paths[self._index]
        self._index += 1
        return path
    
    def __len__(self) -> int:
        """Возвращает количество путей."""
        return len(self._paths)