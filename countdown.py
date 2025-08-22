import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QCalendarWidget, QDialog,
    QHBoxLayout, QSizeGrip, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate, QPoint
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

SETTINGS_FILE = "settings.json"

class TitleDateDialog(QDialog):
    def __init__(self, current_title="", current_date=None):
        super().__init__()
        self.setWindowTitle("Set Countdown Title and Date")
        self.setMinimumWidth(320)
        layout = QVBoxLayout()

        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter countdown title")
        self.title_edit.setText(current_title)
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(self.title_edit)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        if current_date:
            self.calendar.setSelectedDate(QDate(current_date.year, current_date.month, current_date.day))
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.calendar)

        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_title_and_date(self):
        title = self.title_edit.text().strip()
        date = self.calendar.selectedDate().toPyDate()
        return title, date

class CountdownWidget(QWidget):
    def __init__(self):
        super().__init__()

        loaded = self.load_settings()
        self.countdown_title = loaded.get("title", "")
        self.target_date = loaded.get("target_date", datetime(2025, 12, 31, 0, 0, 0))
        self.dragging = False
        self.offset = QPoint()

        self.init_ui()
        self.update_countdown()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

        # If no title or date set, prompt user
        if not self.countdown_title or not loaded.get("target_date"):
            self.pick_title_and_date()

    def init_ui(self):
        self.setWindowTitle("Countdown Widget")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setStyleSheet("""
            QWidget {
                border: none;
            }
            /* Main widget only */
            CountdownWidget {
                background: #fff; /* background: rgba(245, 245, 254, 0.7); */
                border-radius: 32px;      /* More rounded corners */
                border: 2px solid #e6e8ec; /* Subtle border */
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(18)

        # Editable Title
        self.title = QLabel(self.countdown_title or "Countdown")
        self.title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #23272f;")
        main_layout.addWidget(self.title)


        # Date row with calendar icon
        date_row = QHBoxLayout()
        self.date_icon = QLabel()
        self.date_icon.setText("📅")
        self.date_icon.setFont(QFont("Segoe UI Emoji", 14))
        self.date_label = QLabel(self.target_date.strftime("%A, %B %d, %Y at %I:%M %p"))
        self.date_label.setFont(QFont("Segoe UI", 11))
        self.date_label.setStyleSheet("color: #000;")
        date_row.addWidget(self.date_icon)
        date_row.addWidget(self.date_label)
        date_row.addStretch()
        main_layout.addLayout(date_row)

        # Countdown boxes
        self.countdown_row = QHBoxLayout()
        self.countdown_row.setSpacing(18)
        self.boxes = []
        for label in ["Days", "Hours", "Minutes", "Seconds"]:
            box = QVBoxLayout()
            num = QLabel("00")
            num.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            num.setStyleSheet("color: #22223b;")
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text = QLabel(label)
            text.setFont(QFont("Segoe UI", 11))
            text.setStyleSheet("color: #7d8597;")
            text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background: #f0f1f3;
                    border-radius: 16px;
                    border: none;
                }
            """)
            frame.setLayout(QVBoxLayout())
            frame.layout().addWidget(num)
            frame.layout().addWidget(text)
            frame.layout().setContentsMargins(8, 8, 8, 8)
            frame.layout().setSpacing(2)
            box.addWidget(frame)
            self.countdown_row.addLayout(box)
            self.boxes.append(num)
        main_layout.addSpacing(10)
        main_layout.addLayout(self.countdown_row)

        # Change date/title button
        self.button = QPushButton("Change Title/Date")
        self.button.setStyleSheet("""
            QPushButton {
                background: #f6f8fa;
                color: #23272f;
                border-radius: 10px;
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover {
                background: #b0b8c1;
            }
        """)
        self.button.clicked.connect(self.pick_title_and_date)
        main_layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignRight)

        # QSizeGrip for resizing
        size_grip = QSizeGrip(self)
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)
        main_layout.addLayout(grip_layout)
        size_grip.setStyleSheet("background: #b0b8c1; border-radius: 6px;")

        self.setLayout(main_layout)
        self.resize(480, 340)
        self.setMinimumSize(340, 220)

    def pick_title_and_date(self):
        dialog = TitleDateDialog(self.countdown_title, self.target_date)
        if dialog.exec():
            title, picked_date = dialog.get_title_and_date()
            self.countdown_title = title or "Countdown"
            self.target_date = datetime.combine(picked_date, datetime.min.time())
            self.save_settings()
            self.title.setText(self.countdown_title)
            self.date_label.setText(self.target_date.strftime("%A, %B %d, %Y at %I:%M %p"))
            self.update_countdown()

    def get_time_left(self):
        now = datetime.now()
        delta = self.target_date - now
        if delta.total_seconds() < 0:
            return 0, 0, 0, 0
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return days, hours, minutes, seconds

    def update_countdown(self):
        days, hours, minutes, seconds = self.get_time_left()
        values = [days, hours, minutes, seconds]
        for i, num in enumerate(self.boxes):
            num.setText(f"{values[i]:02d}")

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "title": self.countdown_title,
                "target_date": self.target_date.strftime("%Y-%m-%d")
            }, f)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                try:
                    target_date = datetime.strptime(data["target_date"], "%Y-%m-%d")
                except Exception:
                    target_date = None
                return {
                    "title": data.get("title", ""),
                    "target_date": target_date
                }
        return {}

    # --- Mouse Events for Dragging & Closing ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.close()   # Double-click anywhere to close

def main():
    app = QApplication(sys.argv)
    widget = CountdownWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
