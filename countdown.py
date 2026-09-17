import sys
import threading
import time
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QVBoxLayout, QWidget, QColorDialog, QCheckBox
)

try:
    import winsound
except ImportError:
    winsound = None


# ============================================================
# Configurable timer messages
# ============================================================
@dataclass
class TimerMessage:
    name: str
    trigger_seconds: int
    message: str
    color: str
    beep: bool = True
    beep_seconds: int = 5


DEFAULT_MESSAGES = [
    TimerMessage(
        "5 Minutes Left",
        5 * 60,
        "PLEASE PREPARE TO WRAP UP YOUR TALK.",
        "#FFD700",
        True,
        5,
    ),
    TimerMessage(
        "3 Minutes Left",
        3 * 60,
        "YOU HAVE 3 MINUTES LEFT. PLEASE CONTINUE TO WRAP UP.",
        "#FFA500",
        True,
        5,
    ),
    TimerMessage(
        "2 Minutes Left",
        2 * 60,
        "PLEASE WRAP UP YOUR TALK....",
        "#FF3B30",
        True,
        5,
    ),
    TimerMessage(
        "Time's Up",
        0,
        "THANK YOU, UP NEXT AWARDING OF PLAQUE OF APPRECIATION.",
        "#FF0000",
        True,
        5,
    ),
]


def beep_sequence(seconds=5, freq=1000, duration_ms=400):
    if winsound is None:
        return

    def worker():
        for _ in range(seconds):
            try:
                winsound.Beep(freq, duration_ms)
            except RuntimeError:
                pass
            time.sleep(1)

    threading.Thread(target=worker, daemon=True).start()


# ============================================================
# Message Settings Dialog
# ============================================================
class MessageEditorDialog(QDialog):
    def __init__(self, parent=None, message=None, theme=None):
        super().__init__(parent)
        if theme is None and parent is not None:
            theme = getattr(parent, "theme", "dark")
        self.theme = theme or "dark"
        self.setStyleSheet(dialog_theme_stylesheet(self.theme))
        self.setWindowTitle("Timer Message Settings")
        self.setMinimumWidth(520)

        self.name_edit = QLineEdit()
        self.trigger_spin = QSpinBox()
        self.trigger_spin.setRange(0, 24 * 60 * 60)
        self.trigger_spin.setSuffix(" seconds")
        self.message_edit = QLineEdit()
        self.color_edit = QLineEdit()
        self.color_button = QPushButton("Choose Color")
        self.beep_spin = QSpinBox()
        self.beep_spin.setRange(0, 30)
        self.beep_spin.setSuffix(" seconds")

        if message:
            display_name = "DEFAULT" if message.name == "__DEFAULT__" else message.name
            self.name_edit.setText(display_name)
            self.trigger_spin.setValue(max(0, message.trigger_seconds))
            self.message_edit.setText(message.message)
            self.color_edit.setText(message.color)
            self.beep_spin.setValue(message.beep_seconds if message.beep else 0)
        else:
            self.color_edit.setText("#FFFFFF")
            self.beep_spin.setValue(5)

        self.color_button.clicked.connect(self.choose_color)

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Trigger at:", self.trigger_spin)
        form.addRow("Message:", self.message_edit)

        color_row = QHBoxLayout()
        color_row.addWidget(self.color_edit)
        color_row.addWidget(self.color_button)
        form.addRow("Message Color:", color_row)

        form.addRow("Beep Duration:", self.beep_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.color_edit.text()), self)
        if color.isValid():
            self.color_edit.setText(color.name().upper())

    def get_message(self):
        name = self.name_edit.text().strip() or "Timer Message"
        if name.upper() == "DEFAULT":
            name = "Timer Message"

        return TimerMessage(
            name,
            self.trigger_spin.value(),
            self.message_edit.text(),
            self.color_edit.text().strip() or "#FFFFFF",
            self.beep_spin.value() > 0,
            self.beep_spin.value(),
        )


def dialog_theme_stylesheet(theme):
    if theme == "light":
        return """
            QDialog {
                background: #F4F4F4;
                color: #202020;
            }
            QLabel {
                color: #202020;
            }
            QListWidget {
                background: white;
                color: #202020;
                border: 1px solid #BDBDBD;
            }
            QListWidget::item {
                padding: 6px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background: white;
                color: #202020;
                border: 1px solid #BDBDBD;
                padding: 7px;
                border-radius: 5px;
            }
            QCheckBox {
                color: #202020;
            }
            QPushButton {
                background: #E8E8E8;
                color: #202020;
                border: 1px solid #BDBDBD;
                border-radius: 6px;
                padding: 9px 13px;
            }
            QPushButton:hover {
                background: #DCDCDC;
            }
        """
    return """
        QDialog {
            background: #111111;
            color: #F5F5F5;
        }
        QLabel {
            color: #F5F5F5;
        }
        QListWidget {
            background: #222222;
            color: #F5F5F5;
            border: 1px solid #555555;
        }
        QListWidget::item {
            padding: 6px;
        }
        QLineEdit, QSpinBox, QComboBox {
            background: #222222;
            color: white;
            border: 1px solid #555555;
            padding: 7px;
            border-radius: 5px;
        }
        QCheckBox {
            color: #F5F5F5;
        }
        QPushButton {
            background: #2B2B2B;
            color: white;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 9px 13px;
        }
        QPushButton:hover {
            background: #3A3A3A;
        }
    """


# ============================================================
# Settings Window
# ============================================================
class MessageSettingsDialog(QDialog):
    messages_changed = Signal()

    def __init__(self, messages, parent=None, theme="dark"):
        super().__init__(parent)
        self.theme = theme
        self.setStyleSheet(dialog_theme_stylesheet(self.theme))
        self.setWindowTitle("Message Settings")
        self.resize(700, 450)
        self.messages = messages

        self.list = QListWidget()
        self.refresh_list()

        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        default_btn = QPushButton("Edit Default")

        add_btn.clicked.connect(self.add_message)
        edit_btn.clicked.connect(self.edit_message)
        delete_btn.clicked.connect(self.delete_message)
        default_btn.clicked.connect(self.edit_default_message)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(add_btn)
        buttons_row.addWidget(edit_btn)
        buttons_row.addWidget(delete_btn)
        buttons_row.addWidget(default_btn)
        buttons_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Default message is shown while remaining time is ABOVE "
            "the first custom threshold. Custom messages take over when "
            "their configured threshold is reached."
        ))
        layout.addWidget(self.list)
        layout.addLayout(buttons_row)
        layout.addWidget(close_btn)

    def refresh_list(self):
        self.list.clear()

        # DEFAULT follows the controller theme.
        default_color = (
            "#202020" if self.theme == "light" else "#FFFFFF"
        )

        # Configured remaining-time messages always use their own color.
        for m in self.messages:
            if m.name == "__DEFAULT__":
                label = f"DEFAULT  |  {m.message}"
                item_color = default_color
            else:
                label = (
                    f"{m.name}  |  "
                    f"{m.trigger_seconds // 60:02d}:{m.trigger_seconds % 60:02d}  |  "
                    f"{m.message}"
                )
                item_color = m.color

            item = QListWidgetItem(label)
            item.setForeground(QColor(item_color))
            self.list.addItem(item)

    def edit_default_message(self):
        target = next((m for m in self.messages if m.name == "__DEFAULT__"), None)
        if target is None:
            return

        dlg = MessageEditorDialog(self, target, self.theme)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            replacement = dlg.get_message()
            replacement.name = "__DEFAULT__"
            replacement.trigger_seconds = -1
            replacement.beep = False
            replacement.beep_seconds = 0

            index = self.messages.index(target)
            self.messages[index] = replacement
            self.refresh_list()
            self.messages_changed.emit()

    def add_message(self):
        dlg = MessageEditorDialog(self, theme=self.theme)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.messages.append(dlg.get_message())
            self.refresh_list()
            self.messages_changed.emit()

    def edit_message(self):
        row = self.list.currentRow()
        if row < 0:
            return

        target = self.messages[row]

        # DEFAULT is editable, but its trigger is not meaningful.
        dlg = MessageEditorDialog(self, target, self.theme)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            replacement = dlg.get_message()
            index = self.messages.index(target)
            self.messages[index] = replacement
            self.refresh_list()
            self.messages_changed.emit()

    def delete_message(self):
        row = self.list.currentRow()
        if row < 0:
            return

        target = self.messages[row]

        if target.name == "__DEFAULT__":
            QMessageBox.information(
                self,
                "Default Message",
                "The default message cannot be deleted. Edit it instead."
            )
            return

        if QMessageBox.question(
            self,
            "Delete Message",
            f"Delete '{target.name}'?"
        ) == QMessageBox.StandardButton.Yes:
            self.messages.remove(target)
            self.refresh_list()
            self.messages_changed.emit()


# ============================================================
# Full-screen display
# ============================================================
class DisplayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Countdown Display")
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setStyleSheet("background-color: black;")
        self.setMinimumSize(400, 250)

        self.countdown = QLabel("00:00:00")
        self.countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown.setStyleSheet("color: white;")

        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet("color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addStretch(2)
        layout.addWidget(self.countdown, 3)
        layout.addWidget(self.message, 2)
        layout.addStretch(1)

        self.update_fonts()

    def move_to_screen(self, screen, fullscreen=False):
        if not screen:
            return

        geometry = screen.geometry()

        if fullscreen:
            self.showNormal()
            self.setGeometry(geometry)
            self.showFullScreen()
        else:
            self.showNormal()

            # Keep a practical presentation size while allowing dragging.
            width = min(1200, geometry.width() - 100)
            height = min(700, geometry.height() - 100)

            x = geometry.x() + (geometry.width() - width) // 2
            y = geometry.y() + (geometry.height() - height) // 2

            self.setGeometry(x, y, width, height)

        self.raise_()
        self.activateWindow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_fonts()

    def update_fonts(self):
        base = max(200, min(self.width(), self.height()))
        self.countdown.setFont(QFont("Arial", max(30, base // 5)))
        self.message.setFont(QFont("Arial", max(16, base // 14)))


# ============================================================
# Display / Monitor Selection Dialog
# ============================================================
class DisplaySettingsDialog(QDialog):
    def __init__(self, display_window, parent=None):
        super().__init__(parent)
        self.theme = getattr(parent, "theme", "dark") if parent else "dark"
        self.setStyleSheet(dialog_theme_stylesheet(self.theme))
        self.display_window = display_window
        self.setWindowTitle("Display Settings")
        self.resize(600, 430)

        self.monitor_list = QListWidget()
        self.monitor_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )

        self.fullscreen_check = QCheckBox("Show display fullscreen on selected monitor")
        self.fullscreen_check.setChecked(
            display_window.isFullScreen() if display_window else False
        )

        screens = QApplication.screens()
        current_screen = None

        if display_window:
            center = display_window.frameGeometry().center()
            current_screen = QApplication.screenAt(center)

        for index, screen in enumerate(screens):
            geometry = screen.geometry()
            primary = "  [PRIMARY]" if screen == QApplication.primaryScreen() else ""
            item = QListWidgetItem(
                f"Monitor {index + 1}{primary}  —  "
                f"{geometry.width()} × {geometry.height()}  "
                f"({geometry.x()}, {geometry.y()})"
            )
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.monitor_list.addItem(item)

            if screen == current_screen:
                self.monitor_list.setCurrentItem(item)

        if self.monitor_list.currentRow() < 0 and self.monitor_list.count():
            self.monitor_list.setCurrentRow(0)

        preview = QLabel(
            "Select which monitor will show the countdown.\n\n"
            "• Fullscreen ON: fills the selected monitor.\n"
            "• Fullscreen OFF: opens a normal movable window that you can drag "
            "to any monitor."
        )
        preview.setWordWrap(True)

        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        apply_btn.clicked.connect(self.apply_settings)
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(apply_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Display Monitor"))
        layout.addWidget(self.monitor_list)
        layout.addWidget(self.fullscreen_check)
        layout.addWidget(preview)
        layout.addLayout(buttons)

    def apply_settings(self):
        row = self.monitor_list.currentRow()
        if row < 0:
            return

        screen = QApplication.screens()[row]
        fullscreen = self.fullscreen_check.isChecked()

        self.display_window.move_to_screen(screen, fullscreen)
        self.accept()


# ============================================================
# Main application
# ============================================================
class CountdownApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Countdown Control Panel")
        self.resize(850, 600)

        self.time_left = 0
        self.running = False
        self.paused = False
        self.triggered = set()
        # The default message is configurable too.
        # It is used whenever time_left is ABOVE the first custom threshold.
        self.default_message = TimerMessage(
            "__DEFAULT__",
            -1,
            "Time Remaining",
            "#FFFFFF",
            False,
            0,
        )

        self.messages = [
            self.default_message,
            *[
                TimerMessage(**vars(m))
                for m in DEFAULT_MESSAGES
            ],
        ]

        self.theme = "dark"

        self.display_window = None
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.countdown_tick)

        self.build_ui()
        self.update_preview()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------
    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(25, 25, 25, 25)
        root.setSpacing(18)

        # Theme toggle: button only, positioned at the very top.
        theme_row = QHBoxLayout()
        theme_row.addStretch()

        self.theme_btn = QPushButton("Light Mode")
        self.theme_btn.setFixedWidth(120)
        self.theme_btn.clicked.connect(self.toggle_theme)

        theme_row.addWidget(self.theme_btn)
        root.addLayout(theme_row)

        title = QLabel("COUNTDOWN TIMER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        root.addWidget(title)

        time_box = QGroupBox("Set Timer")
        time_grid = QGridLayout(time_box)

        self.hours = QComboBox()
        self.minutes = QComboBox()
        self.seconds = QComboBox()

        self.hours.addItems([str(i) for i in range(13)])
        self.minutes.addItems([str(i) for i in range(60)])
        self.seconds.addItems([str(i) for i in range(60)])

        self.minutes.setCurrentText("5")

        for box in (self.hours, self.minutes, self.seconds):
            box.setEditable(True)
            box.currentTextChanged.connect(self.update_preview)

        time_grid.addWidget(QLabel("Hours"), 0, 0)
        time_grid.addWidget(QLabel("Minutes"), 0, 1)
        time_grid.addWidget(QLabel("Seconds"), 0, 2)
        time_grid.addWidget(self.hours, 1, 0)
        time_grid.addWidget(self.minutes, 1, 1)
        time_grid.addWidget(self.seconds, 1, 2)

        root.addWidget(time_box)

        # Clean controller countdown area.
        # No frame/border; the theme controls the DEFAULT text color,
        # while configured threshold colors remain independent.
        self.countdown_label = QLabel("00:00:00")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setFont(QFont("Arial", 64, QFont.Weight.Bold))
        root.addWidget(self.countdown_label)

        self.message_label = QLabel("Time Remaining")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont("Arial", 20))
        root.addWidget(self.message_label)

        buttons = QHBoxLayout()

        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.reset_btn = QPushButton("Reset")
        self.display_btn = QPushButton("Open Display")
        self.display_settings_btn = QPushButton("Display Settings")
        self.settings_btn = QPushButton("Message Settings")

        self.start_btn.clicked.connect(self.start_countdown)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.reset_btn.clicked.connect(self.reset_countdown)
        self.display_btn.clicked.connect(self.open_display)
        self.display_settings_btn.clicked.connect(self.open_display_settings)
        self.settings_btn.clicked.connect(self.open_settings)

        for b in (
            self.start_btn,
            self.pause_btn,
            self.reset_btn,
            self.display_btn,
            self.display_settings_btn,
            self.settings_btn,
        ):
            buttons.addWidget(b)

        root.addLayout(buttons)

        info = QLabel(
            "Default message is shown above the first custom threshold. "
            "Example: 30:00 → Default; 05:00 and below → Custom. "
            "Use Display Settings to choose Monitor 1, 2, 3, etc., "
            "or open a movable window and drag it to any monitor."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(info)

        self.apply_theme()

    def apply_theme(self):
        """
        Apply the controller theme.

        Theme affects:
        - Controller background
        - Labels/buttons/inputs
        - Preview border
        - DEFAULT message text color

        Configured countdown/message colors are preserved when a custom
        threshold is active.
        """
        if self.theme == "light":
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background: #F4F4F4;
                    color: #202020;
                }
                QGroupBox {
                    border: 1px solid #C8C8C8;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding: 15px;
                    font-weight: bold;
                }
                QComboBox, QLineEdit, QSpinBox {
                    background: white;
                    color: #202020;
                    border: 1px solid #BDBDBD;
                    padding: 8px;
                    border-radius: 5px;
                }
                QListWidget {
                    background: white;
                    color: #202020;
                    border: 1px solid #BDBDBD;
                }
                QPushButton {
                    background: #E8E8E8;
                    color: #202020;
                    border: 1px solid #BDBDBD;
                    border-radius: 6px;
                    padding: 10px 14px;
                }
                QPushButton:hover {
                    background: #DCDCDC;
                }
            """)
            self.theme_btn.setText("Dark Mode")
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background: #111111;
                    color: #F5F5F5;
                }
                QGroupBox {
                    border: 1px solid #444444;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding: 15px;
                    font-weight: bold;
                }
                QComboBox, QLineEdit, QSpinBox {
                    background: #222222;
                    color: white;
                    border: 1px solid #555555;
                    padding: 8px;
                    border-radius: 5px;
                }
                QListWidget {
                    background: #222222;
                    color: white;
                    border: 1px solid #555555;
                }
                QPushButton {
                    background: #2B2B2B;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    padding: 10px 14px;
                }
                QPushButton:hover {
                    background: #3A3A3A;
                }
            """)
            self.theme_btn.setText("Light Mode")

        # Only update the preview color if the current state is DEFAULT.
        # Custom threshold colors remain untouched.
        active = self.get_active_message() if hasattr(self, "messages") else None
        if active is None or active.name == "__DEFAULT__":
            self.apply_default_text_color()

    def apply_default_text_color(self):
        # This function is ONLY for the DEFAULT state.
        # Configured remaining-time colors are never changed by the theme.
        active = self.get_active_message() if hasattr(self, "messages") else None
        if active is not None and active.name != "__DEFAULT__":
            return

        color = "#202020" if self.theme == "light" else "#FFFFFF"
        self.countdown_label.setStyleSheet(f"color: {color};")
        self.message_label.setStyleSheet(f"color: {color};")

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

        # Re-render the current timer state so DEFAULT follows the theme
        # while configured threshold colors remain unchanged.
        if hasattr(self, "time_left"):
            self.trigger_message_if_needed()

    # --------------------------------------------------------
    # Timer helpers
    # --------------------------------------------------------
    def get_dropdown_seconds(self):
        try:
            h = max(0, int(self.hours.currentText()))
            m = max(0, int(self.minutes.currentText()))
            s = max(0, int(self.seconds.currentText()))
            return h * 3600 + m * 60 + s
        except ValueError:
            return 0

    def format_time(self, total):
        total = max(0, total)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_preview(self):
        if self.running:
            return

        self.time_left = self.get_dropdown_seconds()
        self.set_display(
            self.format_time(self.time_left),
            "Time Remaining",
            "#FFFFFF"
        )

    def set_display(self, time_text, message, color):
        self.countdown_label.setText(time_text)
        self.message_label.setText(message)

        # COLOR RULE:
        # 1. DEFAULT only: follows the controller theme.
        #    Dark = white, Light = black.
        # 2. Any configured remaining-time message: use its own configured
        #    color exactly as saved in Message Settings.
        active = self.get_active_message() if hasattr(self, "messages") else None

        if active is not None and active.name == "__DEFAULT__":
            controller_color = "#202020" if self.theme == "light" else "#FFFFFF"
        else:
            controller_color = color

        self.countdown_label.setStyleSheet(
            f"color: {controller_color};"
        )
        self.message_label.setStyleSheet(
            f"color: {controller_color};"
        )

        # External presentation display is independent of the controller
        # theme and always uses the active configured/default display color.
        if self.display_window and self.display_window.isVisible():
            self.display_window.countdown.setText(time_text)
            self.display_window.countdown.setStyleSheet(
                f"color: {color};"
            )
            self.display_window.message.setText(message)
            self.display_window.message.setStyleSheet(
                f"color: {color};"
            )

    # --------------------------------------------------------
    # Message engine
    # --------------------------------------------------------
    def get_default_message(self):
        """
        The default message is shown when the timer is still ABOVE
        the highest configured custom-message threshold.

        Example:
            Timer starts at 30:00
            Custom threshold = 05:00

            30:00 ... 05:01 -> DEFAULT MESSAGE
            05:00 ... 00:00 -> CUSTOM MESSAGE
        """
        defaults = [m for m in self.messages if m.name == "__DEFAULT__"]
        if defaults:
            return defaults[0]

        return TimerMessage(
            "__DEFAULT__",
            -1,
            "Time Remaining",
            "#FFFFFF",
            False,
            0,
        )

    def get_custom_messages(self):
        """Return only threshold-based custom messages."""
        return [
            m for m in self.messages
            if m.name != "__DEFAULT__"
        ]

    def get_active_message(self):
        """
        Select the active message.

        IMPORTANT:
        - Default message applies ABOVE the first custom threshold.
        - Once time_left <= a configured threshold, the matching
          custom message takes over.
        - The closest reached threshold wins.

        Example with custom messages at 5:00 and 2:00:
            > 5:00  -> Default
            <= 5:00 -> 5-minute custom message
            <= 2:00 -> 2-minute custom message
        """
        custom_messages = self.get_custom_messages()

        eligible = [
            m for m in custom_messages
            if self.time_left <= m.trigger_seconds
        ]

        if not eligible:
            return self.get_default_message()

        return max(eligible, key=lambda m: m.trigger_seconds)

    def trigger_message_if_needed(self):
        message = self.get_active_message()

        # Default message does not need a threshold trigger/beep.
        if message.name != "__DEFAULT__":
            if message.trigger_seconds not in self.triggered:
                self.triggered.add(message.trigger_seconds)

                if message.beep and message.beep_seconds > 0:
                    beep_sequence(message.beep_seconds)

        self.set_display(
            self.format_time(self.time_left),
            message.message,
            message.color
        )

    # --------------------------------------------------------
    # Start / pause / reset
    # --------------------------------------------------------
    def start_countdown(self):
        if self.running:
            return

        self.time_left = self.get_dropdown_seconds()
        self.triggered.clear()
        self.running = True
        self.paused = False
        self.pause_btn.setText("Pause")

        self.trigger_message_if_needed()

        if self.time_left <= 0:
            self.finish_timer()
        else:
            self.timer.start()

    def toggle_pause(self):
        if not self.running:
            return

        self.paused = not self.paused

        if self.paused:
            self.timer.stop()
            self.pause_btn.setText("Resume")
        else:
            self.pause_btn.setText("Pause")
            self.timer.start()

    def reset_countdown(self):
        self.timer.stop()
        self.running = False
        self.paused = False
        self.triggered.clear()
        self.time_left = 0
        self.pause_btn.setText("Pause")

        self.set_display(
            "00:00:00",
            "",
            "#202020" if self.theme == "light" else "#FFFFFF"
        )

    def finish_timer(self):
        self.timer.stop()
        self.running = False
        self.paused = False
        self.pause_btn.setText("Pause")
        self.trigger_message_if_needed()

    def countdown_tick(self):
        if not self.running or self.paused:
            return

        # First display the current second, then decrease.
        self.trigger_message_if_needed()

        if self.time_left <= 0:
            self.finish_timer()
            return

        self.time_left -= 1

    # --------------------------------------------------------
    # Display and settings
    # --------------------------------------------------------
    def open_display(self):
        if self.display_window is None:
            self.display_window = DisplayWindow()

        # Open on the monitor currently selected in the system, initially
        # using the primary monitor. The user can change this with
        # "Display Settings".
        screen = QApplication.primaryScreen()
        if screen:
            self.display_window.move_to_screen(screen, fullscreen=False)

        self.trigger_message_if_needed()

    def open_display_settings(self):
        if self.display_window is None:
            self.display_window = DisplayWindow()

        dlg = DisplaySettingsDialog(self.display_window, self)
        dlg.exec()

    def open_settings(self):
        dlg = MessageSettingsDialog(self.messages, self, self.theme)
        dlg.messages_changed.connect(self.on_messages_changed)
        dlg.exec()

    def on_messages_changed(self):
        if not self.running:
            self.trigger_message_if_needed()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Countdown Timer")
    window = CountdownApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
