import argparse
import csv
import random
import time
import re
from pathlib import Path
from typing import Optional, Tuple, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class MixKitScraper:
    """Скрапер для загрузки аудиофайлов с сайта MixKit."""
    
    BASE_URL: str = "https://mixkit.co"
    CATEGORY_URL: str = "https://mixkit.co/free-sound-effects/"
    
    def __init__(self, workers: int = 3) -> None:
        """
        Инициализирует скрапер.
        
        Args:
            workers: Количество рабочих потоков для параллельной обработки.
        """
        self.session: requests.Session = self._create_session()
        self.workers: int = workers
        self.request_delay: float = 1.5
        self.max_retries: int = 5
        self.rate_limit_wait: int = 30
    
    def _create_session(self) -> requests.Session:
        """Создает и настраивает HTTP-сессию."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://mixkit.co/',
        })
        return session
    
    def _rate_limit_delay(self) -> None:
        """Задержка для соблюдения лимита запросов."""
        time.sleep(random.uniform(self.request_delay, self.request_delay * 1.5))
    
    def _handle_rate_limit(self, attempt: int) -> None:
        """Обработка ограничения запросов."""
        wait_time = self.rate_limit_wait * (attempt + 1)
        print(f"[WARNING] Обнаружено ограничение запросов. Ждем {wait_time} секунд...")
        time.sleep(wait_time)
    
    def get_sound_links(self, num_pages: int) -> List[str]:
        """
        Получает ссылки на звуковые карточки с указанного количества страниц.
        
        Args:
            num_pages: Количество страниц для парсинга.
            
        Returns:
            Список URL-адресов звуковых карточек.
        """
        links: Set[str] = set()
        
        print(f"[INFO] Парсинг {num_pages} страниц для получения ссылок...")
        
        for page_num in range(1, num_pages + 1):
            for attempt in range(self.max_retries):
                try:
                    time.sleep(random.uniform(2.0, 3.0))
                    
                    url = f"{self.CATEGORY_URL}?page={page_num}"
                    
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Основной поиск карточек
                    card_selectors = [
                        'a[href^="/free-sound-effects/"]',
                        'div.item-grid-card a',
                        'article a[href^="/free-sound-effects/"]',
                    ]
                    
                    all_links = []
                    for selector in card_selectors:
                        found_links = soup.select(selector)
                        all_links.extend(found_links)
                    
                    # Убираем дубликаты и фильтруем
                    page_links_count = 0
                    for link in all_links:
                        href = link.get('href')
                        if href and href.startswith('/free-sound-effects/') and href != '/free-sound-effects/':
                            # Пропускаем категории (ссылки с подкатегориями)
                            if len(href.strip('/').split('/')) <= 3:  # Только прямые ссылки на аудио
                                full_url = f"{self.BASE_URL}{href}"
                                if full_url not in links:
                                    links.add(full_url)
                                    page_links_count += 1
                    
                    print(f"[INFO] Страница {page_num}: найдено {page_links_count} карточек")
                    
                    # Проверяем, есть ли карточки на странице
                    if page_links_count == 0 and page_num > 1:
                        print(f"[INFO] На странице {page_num} нет карточек. Возможно, достигнут конец списка.")
                        return list(links)
                    
                    break
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        self._handle_rate_limit(attempt)
                        if attempt == self.max_retries - 1:
                            print(f"[ERROR] Не удалось обработать страницу {page_num} после {self.max_retries} попыток")
                    else:
                        print(f"[ERROR] Ошибка HTTP на странице {page_num}: {e}")
                        break
                except Exception as e:
                    print(f"[ERROR] Ошибка при парсинге страницы {page_num}: {e}")
                    break
        
        print(f"[INFO] Всего найдено {len(links)} уникальных карточек")
        return list(links)
    
    def extract_audio_info(self, card_url: str) -> Optional[Tuple[str, int]]:
        """
        Извлекает информацию об аудиофайле из карточки.
        
        Args:
            card_url: URL карточки с аудио.
            
        Returns:
            Кортеж (URL аудиофайла, длительность в секундах) или None в случае ошибки.
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit_delay()
                
                response = self.session.get(card_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Поиск URL аудиофайла
                audio_url = self._find_audio_url(soup, response.text)
                if not audio_url:
                    return None
                
                # Проверяем, что это WAV файл
                if not audio_url.lower().endswith('.wav'):
                    return None
                
                # Извлечение длительности
                duration = self._extract_duration(soup)
                
                return audio_url, duration
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    self._handle_rate_limit(attempt)
                    if attempt == self.max_retries - 1:
                        return None
                else:
                    return None
            except Exception:
                return None
        
        return None
    
    def _find_audio_url(self, soup: BeautifulSoup, page_text: str) -> Optional[str]:
        """Ищет URL аудиофайла."""
        
        # Способ 1: через модальное окно
        modal_button = soup.find(attrs={'data-download--button-modal-url-value': True})
        if modal_button:
            modal_path = modal_button['data-download--button-modal-url-value']
            audio_url = self._get_audio_from_modal(modal_path)
            if audio_url:
                return audio_url
        
        # Способ 2: через атрибут превью
        preview_div = soup.find(attrs={'data-audio-player-preview-url-value': True})
        if preview_div:
            return preview_div['data-audio-player-preview-url-value']
        
        # Способ 3: поиск в тексте страницы (только WAV)
        audio_patterns = [
            r'(https://assets\.mixkit\.co/[^\s"<>]+?\.wav)',
            r'(https?://[^\s"<>]+?\.wav)',
        ]
        
        for pattern in audio_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                return matches[0]
        
        return None
    
    def _get_audio_from_modal(self, modal_path: str) -> Optional[str]:
        """Получает URL аудиофайла из модального окна."""
        for attempt in range(self.max_retries):
            try:
                time.sleep(random.uniform(1.0, 2.0))
                url = f"{self.BASE_URL}{modal_path if modal_path.startswith('/') else '/' + modal_path}"
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Ищем WAV файлы
                matches = re.findall(r'(https?://[^\s"<>]+?\.wav)', response.text)
                return matches[0] if matches else None
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    self._handle_rate_limit(attempt)
                    continue
                else:
                    return None
            except Exception:
                return None
        
        return None
    
    def _extract_duration(self, soup: BeautifulSoup) -> int:
        """Извлекает длительность аудиофайла в секундах."""
        duration_selectors = [
            '[data-test-id="duration"]',
            '.sound__duration',
            '.item-grid-card__duration',
            '.duration',
        ]
        
        for selector in duration_selectors:
            duration_tag = soup.select_one(selector)
            if duration_tag:
                text = duration_tag.get_text(strip=True)
                
                # Формат MM:SS
                if ':' in text:
                    parts = text.split(':')
                    if len(parts) == 2:
                        try:
                            return int(parts[0]) * 60 + int(parts[1])
                        except ValueError:
                            continue
                
                # Просто число (секунды)
                match = re.search(r'(\d+)', text)
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
        
        return 0
    
    def download_audio(self, audio_url: str, save_path: Path, max_retries: int = 5) -> bool:
        """
        Скачивает аудиофайл.
        
        Args:
            audio_url: URL аудиофайла.
            save_path: Путь для сохранения файла.
            max_retries: Максимальное количество попыток.
            
        Returns:
            True если скачивание успешно, иначе False.
        """
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(1.0, 2.0))
                
                with self.session.get(audio_url, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(save_path, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                
                # Проверяем, что файл скачался
                if save_path.exists() and save_path.stat().st_size > 0:
                    return True
                else:
                    save_path.unlink(missing_ok=True)
                    return False
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    print(f"[WARNING] Ограничение запросов. Ждем {wait_time} секунд...")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    pass  # Не выводим ошибку, просто возвращаем False
            except Exception:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    pass  # Не выводим ошибку, просто возвращаем False
        
        return False
    
    def save_annotation(self, annotations: List[Tuple[str, str]], csv_path: Path) -> None:
        """
        Сохраняет аннотации в CSV-файл.
        
        Args:
            annotations: Список кортежей (абсолютный_путь, относительный_путь).
            csv_path: Путь для сохранения CSV-файла.
        """
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=['absolute_path', 'relative_path']
                )
                writer.writeheader()
                
                for absolute_path, relative_path in annotations:
                    writer.writerow({
                        'absolute_path': absolute_path,
                        'relative_path': relative_path
                    })
            
            print(f"[INFO] Аннотации сохранены в {csv_path}")
            
        except Exception as e:
            print(f"[ERROR] Ошибка при сохранении аннотаций: {e}")
    
    def scrape_audio_files(
        self,
        min_duration: int,
        max_files: int,
        save_dir: Path,
        annotation_path: Path,
        num_pages: int
    ) -> int:
        """
        Основная функция скрапинга аудиофайлов.
        
        Args:
            min_duration: Минимальная длительность файлов в секундах.
            max_files: Максимальное количество файлов для скачивания.
            save_dir: Директория для сохранения файлов.
            annotation_path: Путь для сохранения аннотаций.
            num_pages: Количество страниц для парсинга.
            
        Returns:
            Количество успешно скачанных файлов.
        """
        print(f"[INFO] Начало скрапинга WAV файлов:")
        print(f"  - Минимальная длительность: {min_duration} сек")
        print(f"  - Максимальное количество файлов: {max_files}")
        print(f"  - Директория сохранения: {save_dir}")
        print(f"  - Файл аннотаций: {annotation_path}")
        print(f"  - Количество страниц: {num_pages}")
        print(f"  - Рабочие потоки: {self.workers}")
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Получаем ссылки на карточки
        card_links = self.get_sound_links(num_pages)
        
        if not card_links:
            print("[ERROR] Не удалось получить ссылки на карточки")
            return 0
        
        print(f"[INFO] Получено {len(card_links)} уникальных карточек")
        
        # Перемешиваем для разнообразия
        random.shuffle(card_links)
        
        # Обрабатываем больше карточек
        cards_to_process = min(len(card_links), max_files * 5)
        card_links_subset = card_links[:cards_to_process]
        
        print(f"[INFO] Будет обработано {len(card_links_subset)} карточек")
        
        annotations: List[Tuple[str, str]] = []
        processed_urls: Set[str] = set()
        
        # Уменьшаем потоки для стабильности
        actual_workers = min(self.workers, 2)
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = {
                executor.submit(self.extract_audio_info, url): url
                for url in card_links_subset
            }
            
            progress_bar = tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Обработка карточек",
                unit="карточка"
            )
            
            wav_found = 0
            for future in progress_bar:
                if len(annotations) >= max_files:
                    break
                
                info = future.result()
                if not info:
                    continue
                
                audio_url, duration = info
                
                # Уже проверяем только WAV в extract_audio_info
                wav_found += 1
                
                if duration < min_duration:
                    continue
                
                if audio_url in processed_urls:
                    continue
                processed_urls.add(audio_url)
                
                # Формируем имя файла
                filename = audio_url.split('/')[-1].split('?')[0]
                if not filename.lower().endswith('.wav'):
                    filename += '.wav'
                
                save_path = save_dir / filename
                
                # Уникальное имя файла
                counter = 1
                original_stem = save_path.stem
                while save_path.exists():
                    save_path = save_dir / f"{original_stem}_{counter}.wav"
                    counter += 1
                
                print(f"[INFO] Скачивание ({len(annotations)+1}/{max_files}): {save_path.name} ({duration} сек)")
                
                if self.download_audio(audio_url, save_path):
                    absolute_path = str(save_path.resolve())
                    relative_path = str(save_path)
                    
                    annotations.append((absolute_path, relative_path))
                    
                    print(f"[SUCCESS] Скачан WAV: {save_path.name}")
                    progress_bar.set_postfix({
                        'скачано': len(annotations),
                        'wav найдено': wav_found
                    })
                
                # Задержка между скачиваниями
                if len(annotations) < max_files:
                    time.sleep(random.uniform(2.0, 3.0))
        
        # Сохраняем аннотации
        if annotations:
            self.save_annotation(annotations, annotation_path)
        
        print(f"\n[SUMMARY] Итоги:")
        print(f"  - Обработано карточек: {len(card_links_subset)}")
        print(f"  - Найдено WAV файлов: {wav_found}")
        print(f"  - Скачано WAV файлов: {len(annotations)}")
        
        return len(annotations)