"""
Главный модуль приложения для просмотра аудиодатасета.
Содержит графический интерфейс для загрузки и воспроизведения аудиофайлов.
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont

from iterator import AudioPathIterator


class AudioPlayerApp(QMainWindow):
    """Главное окно приложения для просмотра аудиодатасета."""

    def __init__(self) -> None:
        """
        Инициализирует главное окно приложения.
        
        Инициализирует интерфейс, аудиоплеер и управляющие переменные.
        """
        super().__init__()
        
        self.iterator: Optional[AudioPathIterator] = None
        self.current_index: int = 0
        self.audio_files: list[str] = []
        self.is_playing: bool = False
        
        self._init_ui()
        self._init_audio_player()
    
    def _init_ui(self) -> None:
        """
        Инициализирует графический интерфейс.
        
        Создает и настраивает все виджеты, layout'ы и стили.
        """
        self.setWindowTitle("Audio Dataset Viewer")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        self._create_control_panel(main_layout)
        self._create_source_label(main_layout)
        self._create_track_info_section(main_layout)
        self._create_player_controls(main_layout)
        
        central_widget.setLayout(main_layout)
        
        self._init_progress_timer()
    
    def _create_control_panel(self, parent_layout: QVBoxLayout) -> None:
        """
        Создает панель управления для загрузки данных.
        
        Args:
            parent_layout: Родительский layout для добавления виджетов.
        """
        control_panel = QHBoxLayout()
        
        self.load_folder_btn = QPushButton("Загрузить папку")
        self.load_folder_btn.clicked.connect(self._load_folder)
        self.load_folder_btn.setMinimumHeight(40)
        
        self.load_csv_btn = QPushButton("Загрузить CSV")
        self.load_csv_btn.clicked.connect(self._load_csv)
        self.load_csv_btn.setMinimumHeight(40)
        
        control_panel.addWidget(self.load_folder_btn)
        control_panel.addWidget(self.load_csv_btn)
        
        parent_layout.addLayout(control_panel)
    
    def _create_source_label(self, parent_layout: QVBoxLayout) -> None:
        """
        Создает метку для отображения текущего источника данных.
        
        Args:
            parent_layout: Родительский layout для добавления виджетов.
        """
        self.source_label = QLabel("Источник не выбран")
        self.source_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border-radius: 5px;"
        )
        self.source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        parent_layout.addWidget(self.source_label)
    
    def _create_track_info_section(self, parent_layout: QVBoxLayout) -> None:
        """
        Создает секцию с информацией о текущем треке.
        
        Args:
            parent_layout: Родительский layout для добавления виджетов.
        """
        track_info_layout = QVBoxLayout()
        
        self.track_title = QLabel("Название композиции")
        self.track_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.track_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.duration_label = QLabel("Длительность: --:--")
        self.duration_label.setFont(QFont("Arial", 12))
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.file_path_label = QLabel("Путь: не выбран")
        self.file_path_label.setFont(QFont("Arial", 10))
        self.file_path_label.setStyleSheet("color: #666;")
        self.file_path_label.setWordWrap(True)
        
        track_info_layout.addWidget(self.track_title)
        track_info_layout.addWidget(self.duration_label)
        track_info_layout.addWidget(self.file_path_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        parent_layout.addLayout(track_info_layout)
        parent_layout.addWidget(self.progress_bar)
    
    def _create_player_controls(self, parent_layout: QVBoxLayout) -> None:
        """
        Создает панель управления воспроизведением.
        
        Args:
            parent_layout: Родительский layout для добавления виджетов.
        """
        player_controls = QHBoxLayout()
        player_controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.clicked.connect(self._prev_track)
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.setEnabled(False)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setStyleSheet("font-size: 20px;")
        self.play_btn.setEnabled(False)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.clicked.connect(self._next_track)
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.setEnabled(False)
        
        player_controls.addWidget(self.prev_btn)
        player_controls.addWidget(self.play_btn)
        player_controls.addWidget(self.next_btn)
        
        self.track_info = QLabel("Трек 0 из 0")
        self.track_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Готово к загрузке")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 5px;")
        
        parent_layout.addLayout(player_controls)
        parent_layout.addWidget(self.track_info)
        parent_layout.addWidget(self.status_label)
    
    def _init_progress_timer(self) -> None:
        """Инициализирует таймер для обновления прогресса воспроизведения."""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
    
    def _init_audio_player(self) -> None:
        """Инициализирует аудиоплеер и настраивает сигналы."""
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_player_error)
    
    def _load_folder(self) -> None:
        """Загружает аудиофайлы из выбранной пользователем папки."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Выберите папку с аудиофайлами"
        )
        
        if not folder_path:
            return
        
        try:
            self.iterator = AudioPathIterator(folder_path)
            self.audio_files = list(self.iterator)
            self.current_index = 0
            
            self.source_label.setText(f"Папка: {folder_path}")
            self._update_controls()
            self._load_current_track()
            
            if self.audio_files:
                message = f"Загружено {len(self.audio_files)} треков"
            else:
                message = "В папке нет аудиофайлов"
            
            self.status_label.setText(message)
            
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить папку: {str(e)}")
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Неизвестная ошибка", 
                f"Произошла неизвестная ошибка: {str(e)}"
            )
    
    def _load_csv(self) -> None:
        """Загружает аудиофайлы из выбранного CSV-файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            self.iterator = AudioPathIterator(file_path)
            self.audio_files = list(self.iterator)
            self.current_index = 0
            
            self.source_label.setText(f"CSV файл: {Path(file_path).name}")
            self._update_controls()
            self._load_current_track()
            
            if self.audio_files:
                message = f"Загружено {len(self.audio_files)} треков из CSV"
            else:
                message = "В CSV нет аудиофайлов"
            
            self.status_label.setText(message)
            
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить CSV: {str(e)}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Неизвестная ошибка",
                f"Произошла неизвестная ошибка: {str(e)}"
            )
    
    def _load_current_track(self) -> None:
        """Загружает и отображает текущий аудиотрек."""
        if not self.audio_files or self.current_index >= len(self.audio_files):
            return
        
        self.player.stop()
        self.is_playing = False
        self.play_btn.setText("▶")
        
        current_file = self.audio_files[self.current_index]
        
        try:
            file_path = Path(current_file)
            self.track_title.setText(file_path.stem)
            self.file_path_label.setText(f"Путь: {current_file}")
            self.track_info.setText(
                f"Трек {self.current_index + 1} из {len(self.audio_files)}"
            )
            
            self.player.setSource(QUrl.fromLocalFile(current_file))
            self.progress_bar.setValue(0)
            self.duration_label.setText("Длительность: загрузка...")
            
            self.status_label.setText(f"Загружен: {file_path.name}")
            
        except Exception as e:
            self.status_label.setText(f"Ошибка загрузки файла: {str(e)}")
    
    def _toggle_play(self) -> None:
        """Включает или выключает воспроизведение текущего трека."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.is_playing = False
            self.play_btn.setText("▶")
            self.status_label.setText("Пауза")
        else:
            self.player.play()
            self.is_playing = True
            self.play_btn.setText("⏸")
            self.status_label.setText("Воспроизведение")
            self.progress_bar.setVisible(True)
    
    def _next_track(self) -> None:
        """Переключает на следующий трек."""
        if not self.audio_files:
            return
        
        self.player.stop()
        self.is_playing = False
        
        self.current_index = (self.current_index + 1) % len(self.audio_files)
        self._load_current_track()
        
        if self.is_playing:
            self.player.play()
    
    def _prev_track(self) -> None:
        """Переключает на предыдущий трек."""
        if not self.audio_files:
            return
        
        self.player.stop()
        self.is_playing = False
        
        self.current_index = (self.current_index - 1) % len(self.audio_files)
        self._load_current_track()
        
        if self.is_playing:
            self.player.play()
    
    def _update_controls(self) -> None:
        """Обновляет состояние кнопок управления в зависимости от наличия треков."""
        has_tracks = len(self.audio_files) > 0
        
        self.play_btn.setEnabled(has_tracks)
        self.next_btn.setEnabled(has_tracks and len(self.audio_files) > 1)
        self.prev_btn.setEnabled(has_tracks and len(self.audio_files) > 1)
        
        if has_tracks:
            self.progress_bar.setVisible(True)
    
    def _on_duration_changed(self, duration: int) -> None:
        """
        Обрабатывает изменение длительности трека.
        
        Args:
            duration: Длительность трека в миллисекундах.
        """
        if duration > 0:
            minutes = duration // 60000
            seconds = (duration % 60000) // 1000
            self.duration_label.setText(f"Длительность: {minutes:02d}:{seconds:02d}")
            self.progress_bar.setMaximum(duration)
    
    def _on_position_changed(self, position: int) -> None:
        """
        Обновляет позицию прогресс-бара в соответствии с текущей позицией воспроизведения.
        
        Args:
            position: Текущая позиция воспроизведения в миллисекундах.
        """
        if self.player.duration() > 0:
            self.progress_bar.setValue(position)
    
    def _update_progress(self) -> None:
        """Обновляет прогресс воспроизведения через таймер."""
        if self.player.isPlaying():
            current = self.player.position()
            total = self.player.duration()
            if total > 0:
                self.progress_bar.setValue(current)
    
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """
        Обрабатывает изменение состояния воспроизведения.
        
        Args:
            state: Новое состояние воспроизведения.
        """
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_btn.setText("▶")
            self.is_playing = False
            self.status_label.setText("Остановлено")
    
    def _on_player_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        """
        Обрабатывает ошибки аудиоплеера.
        
        Args:
            error: Код ошибки.
            error_string: Текстовое описание ошибки.
        """
        self.status_label.setText(f"Ошибка аудио: {error_string}")
        QMessageBox.warning(
            self,
            "Ошибка аудио",
            f"Не удалось воспроизвести файл: {error_string}"
        )
    
    def closeEvent(self, event) -> None:
        """
        Обрабатывает событие закрытия окна.
        
        Args:
            event: Событие закрытия окна.
        """
        self.player.stop()
        event.accept()


def main() -> None:
    """
    Главная функция приложения.
    
    Инициализирует приложение Qt, создает и отображает главное окно.
    """
    app = QApplication(sys.argv)
    window = AudioPlayerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()