import os
import json
import webbrowser
from ctypes import wintypes
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QFrame, QMessageBox, QStackedWidget,
    QCheckBox
)
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QPixmap

class MainWindow(QMainWindow):
    """
    DIL DIL Voice Assistant Dashboard.
    Clean, lightweight desktop control panel focusing strictly on:
    1. Push-to-Talk Hotkey
    2. Output Language
    3. Gemini API Key & Background Tray execution.
    Styled with the iconic Pakistan flag green, pure white, and sleek black.
    """
    def __init__(self, config_path: str, on_config_updated=None, on_quit=None, on_tray_notify=None):
        super().__init__()
        self.config_path = config_path
        self.on_config_updated = on_config_updated
        self.on_quit = on_quit
        self.on_tray_notify = on_tray_notify
        self.config = self._load_config()

        self._init_window()
        self._init_ui()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "gemini_api_key": "",
            "hotkey": "ctrl+shift",
            "target_language": "english",
            "minimize_to_tray": True
        }

    def _init_window(self):
        self.setWindowTitle("DIL DIL")
        self.setFixedSize(540, 285)

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QMainWindow {
                background-color: #070a0e;
                color: #ffffff;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLabel {
                color: #94a3b8;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: #0f1720;
                color: #ffffff;
                border: 1px solid #1a2f24;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #10b981;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #0f1720;
                color: #ffffff;
                selection-background-color: #059669;
                selection-color: #ffffff;
                border: 1px solid #1a2f24;
                border-radius: 6px;
                padding: 4px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #234233;
                background-color: #0f1720;
            }
            QCheckBox::indicator:checked {
                background-color: #059669;
                border-color: #10b981;
            }
            QPushButton#primaryBtn {
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton#primaryBtn:hover {
                background-color: #10b981;
            }
            QPushButton#primaryBtn:pressed {
                background-color: #047857;
            }
            QPushButton#secondaryBtn {
                background-color: #0f1720;
                color: #ffffff;
                border: 1px solid #1a2f24;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #15222e;
                border-color: #10b981;
                color: #ffffff;
            }
            QPushButton#quitBtn {
                background-color: rgba(239, 68, 68, 0.12);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.28);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#quitBtn:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
            QPushButton#linkBtn {
                background: transparent;
                color: #34d399;
                text-decoration: underline;
                border: none;
                padding: 0;
                text-align: left;
                font-size: 11px;
            }
            QPushButton#linkBtn:hover {
                color: #6ee7b7;
            }
        """)

    def _init_ui(self):
        self.stack = QStackedWidget(self)
        self.stack.setStyleSheet("background-color: #070a0e; border: none;")
        self.stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(self.stack)

        # Page 0: First-time Onboarding (shown if no API key)
        self.onboarding_page = self._create_onboarding_page()
        self.stack.addWidget(self.onboarding_page)

        # Page 1: Main Dashboard (shown when API key is set)
        self.dashboard_page = self._create_dashboard_page()
        self.stack.addWidget(self.dashboard_page)

        has_key = bool(self.config.get("gemini_api_key", "").strip())
        self.stack.setCurrentIndex(1 if has_key else 0)

    def _create_onboarding_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background-color: #070a0e;")
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("🎙️ Welcome to DIL DIL")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Fast, intelligent AI voice dictation directly into any application.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet("background-color: #0d131a; border: 1px solid #16261e; border-radius: 8px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        card_title = QLabel("🔑 Free Gemini API Key Required")
        card_title.setStyleSheet("color: #e2e8f0; font-weight: 600; font-size: 12px;")
        card_desc = QLabel(
            "Powered by Google Gemini. Google provides a permanent free tier with <b>1,500 requests per day</b> at zero cost."
        )
        card_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        card_desc.setWordWrap(True)

        link_btn = QPushButton("👉 Click here to get your free API key from Google AI Studio")
        link_btn.setObjectName("linkBtn")
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))

        card_layout.addWidget(card_title)
        card_layout.addWidget(card_desc)
        card_layout.addWidget(link_btn)
        layout.addWidget(card)

        self.onboarding_key_input = QLineEdit()
        self.onboarding_key_input.setPlaceholderText("Paste your Gemini API key here...")
        self.onboarding_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.onboarding_key_input)

        save_btn = QPushButton("Save & Start Dictating")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_onboarding_key)
        layout.addWidget(save_btn)

        layout.addStretch()
        return page

    def _create_dashboard_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background-color: #070a0e;")
        page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header Bar
        header = QHBoxLayout()
        title_box = QHBoxLayout()
        title_box.setSpacing(8)

        title_icon = QLabel()
        icon_path = os.path.join(os.path.dirname(self.config_path), "assets", "icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            title_icon.setPixmap(pix)
        else:
            title_icon.setText("🎙️")
            title_icon.setStyleSheet("font-size: 18px;")

        title_text = QLabel("DIL DIL")
        title_text.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")
        title_box.addWidget(title_icon)
        title_box.addWidget(title_text)

        status_badge = QLabel("● ACTIVE")
        status_badge.setStyleSheet(
            "background-color: rgba(16, 185, 129, 0.16); color: #10b981; "
            "padding: 2px 8px; border-radius: 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; border: 1px solid rgba(16, 185, 129, 0.3);"
        )

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(status_badge)
        layout.addLayout(header)

        # Settings Row (Side-by-Side: Hotkey & Output Language)
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)

        # Card 1: Push-to-Talk Hotkey
        hotkey_card = QFrame()
        hotkey_card.setStyleSheet("background-color: #0d131a; border: 1px solid #16261e; border-radius: 8px;")
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setContentsMargins(10, 8, 10, 8)
        hotkey_layout.setSpacing(5)

        hotkey_title_row = QHBoxLayout()
        hotkey_title = QLabel("Push-to-Talk Hotkey")
        hotkey_title.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: 600;")
        hotkey_title_row.addWidget(hotkey_title)
        hotkey_title_row.addStretch()

        self.badges_layout = QHBoxLayout()
        self.badges_layout.setSpacing(2)
        hotkey_title_row.addLayout(self.badges_layout)
        hotkey_layout.addLayout(hotkey_title_row)

        self.hotkey_combo = QComboBox()
        self.hotkey_options = [
            ("Ctrl + Shift (Default)", "ctrl+shift"),
            ("Ctrl (Hold Single Key)", "ctrl"),
            ("Alt + Space", "alt+space"),
            ("Ctrl + Space", "ctrl+space"),
            ("Shift + Space", "shift+space"),
            ("F8 (Function Key)", "f8"),
            ("F9 (Function Key)", "f9"),
            ("Custom Combination...", "custom")
        ]
        for name, val in self.hotkey_options:
            self.hotkey_combo.addItem(name, val)

        current_hk = self.config.get("hotkey", "ctrl+shift").lower().strip()
        matched_idx = -1
        for i in range(self.hotkey_combo.count()):
            if self.hotkey_combo.itemData(i) == current_hk:
                matched_idx = i
                break
        if matched_idx >= 0:
            self.hotkey_combo.setCurrentIndex(matched_idx)
        else:
            self.hotkey_combo.setCurrentIndex(self.hotkey_combo.count() - 1)

        self.hotkey_combo.currentIndexChanged.connect(self._on_hotkey_combo_changed)
        hotkey_layout.addWidget(self.hotkey_combo)

        self.custom_hotkey_input = QLineEdit()
        self.custom_hotkey_input.setPlaceholderText("e.g. ctrl+alt, f10")
        self.custom_hotkey_input.setText(current_hk if matched_idx < 0 else "")
        self.custom_hotkey_input.setVisible(matched_idx < 0)
        self.custom_hotkey_input.editingFinished.connect(self._on_custom_hotkey_submitted)
        hotkey_layout.addWidget(self.custom_hotkey_input)

        hotkey_desc = QLabel("Hold to talk. Release to paste.")
        hotkey_desc.setStyleSheet("color: #64748b; font-size: 10px;")
        hotkey_layout.addWidget(hotkey_desc)
        settings_row.addWidget(hotkey_card, 1)

        self._update_hotkey_badges(current_hk)

        # Card 2: Target Language
        lang_card = QFrame()
        lang_card.setStyleSheet("background-color: #0d131a; border: 1px solid #16261e; border-radius: 8px;")
        lang_layout = QVBoxLayout(lang_card)
        lang_layout.setContentsMargins(10, 8, 10, 8)
        lang_layout.setSpacing(5)

        lang_header = QLabel("Output Language")
        lang_header.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: 600;")
        lang_layout.addWidget(lang_header)

        self.lang_combo = QComboBox()
        languages = [
            ("🇬🇧 English (Fluent & Clean)", "english"),
            ("🇵🇰 Urdu (اردو رسم الخط)", "urdu"),
            ("🔤 Roman Urdu (Latin Alphabet)", "roman_urdu"),
            ("🇸🇦 Arabic (العربية)", "arabic"),
            ("🇮🇳 Hindi (हिंदी)", "hindi"),
            ("🇪🇸 Spanish (Español)", "spanish"),
            ("🇫🇷 French (Français)", "french"),
            ("🇩🇪 German (Deutsch)", "german"),
            ("🇧🇷 Portuguese (Português)", "portuguese"),
            ("🇷🇺 Russian (Русский)", "russian"),
            ("🇨🇳 Chinese (Mandarin 简体中文)", "chinese"),
            ("🇯🇵 Japanese (日本語)", "japanese"),
            ("🇹🇷 Turkish (Türkçe)", "turkish"),
            ("🇮🇹 Italian (Italiano)", "italian"),
            ("🇮🇷 Persian (فارسی)", "persian"),
            ("🇵🇰 Punjabi (پنجابی)", "punjabi"),
            ("🇧🇩 Bengali (বাংলা)", "bengali"),
            ("🇳🇱 Dutch (Nederlands)", "dutch"),
            ("🇮🇩 Indonesian (Bahasa Indonesia)", "indonesian"),
        ]
        for display_name, code in languages:
            self.lang_combo.addItem(display_name, code)

        current_lang = self.config.get("target_language", "english")
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == current_lang:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)

        lang_desc = QLabel("Translates speech into selected language.")
        lang_desc.setStyleSheet("color: #64748b; font-size: 10px;")
        lang_layout.addWidget(lang_desc)
        settings_row.addWidget(lang_card, 1)

        layout.addLayout(settings_row)

        # API Key Card (Horizontal Bar)
        api_card = QFrame()
        api_card.setStyleSheet("background-color: #0d131a; border: 1px solid #16261e; border-radius: 8px;")
        api_layout = QHBoxLayout(api_card)
        api_layout.setContentsMargins(10, 6, 10, 6)
        api_layout.setSpacing(6)

        api_title = QLabel("Gemini Key:")
        api_title.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: 600;")
        api_layout.addWidget(api_title)

        self.dashboard_key_input = QLineEdit()
        self.dashboard_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.dashboard_key_input.setText(self.config.get("gemini_api_key", ""))
        self.dashboard_key_input.setPlaceholderText("Enter Gemini API key...")
        api_layout.addWidget(self.dashboard_key_input, 1)

        update_btn = QPushButton("Save")
        update_btn.setObjectName("secondaryBtn")
        update_btn.clicked.connect(self._save_dashboard_key)
        api_layout.addWidget(update_btn)

        get_key_link = QPushButton("Get Free Key")
        get_key_link.setObjectName("linkBtn")
        get_key_link.setCursor(Qt.CursorShape.PointingHandCursor)
        get_key_link.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        api_layout.addWidget(get_key_link)

        layout.addWidget(api_card)

        # Bottom Actions Bar
        bottom_bar = QHBoxLayout()
        self.tray_checkbox = QCheckBox("Keep running in tray on close")
        self.tray_checkbox.setChecked(self.config.get("minimize_to_tray", True))
        self.tray_checkbox.stateChanged.connect(self._on_tray_toggle_changed)
        bottom_bar.addWidget(self.tray_checkbox)

        bottom_bar.addStretch()

        self.hide_tray_btn = QPushButton("Hide to Tray")
        self.hide_tray_btn.setObjectName("secondaryBtn")
        self.hide_tray_btn.clicked.connect(self._hide_to_tray)
        bottom_bar.addWidget(self.hide_tray_btn)

        quit_btn = QPushButton("Close App")
        quit_btn.setObjectName("quitBtn")
        quit_btn.clicked.connect(self._on_close_clicked)
        bottom_bar.addWidget(quit_btn)

        layout.addLayout(bottom_bar)
        return page

    def _update_hotkey_badges(self, hotkey_str: str):
        while self.badges_layout.count():
            item = self.badges_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        parts = [p.strip().upper() for p in hotkey_str.replace("+", " ").replace("-", " ").split() if p.strip()]
        for i, part in enumerate(parts):
            badge = QLabel(part)
            badge.setStyleSheet(
                "background-color: #0b1a13; color: #ffffff; padding: 2px 6px; "
                "border-radius: 4px; font-weight: 700; font-size: 10px; border: 1px solid #10b981;"
            )
            self.badges_layout.addWidget(badge)
            if i < len(parts) - 1:
                plus = QLabel("+")
                plus.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 700;")
                self.badges_layout.addWidget(plus)

    def _on_hotkey_combo_changed(self):
        val = self.hotkey_combo.currentData()
        if val == "custom":
            self.custom_hotkey_input.setVisible(True)
            self.custom_hotkey_input.setFocus()
        else:
            self.custom_hotkey_input.setVisible(False)
            self.config["hotkey"] = val
            self._save_config()
            self._update_hotkey_badges(val)
            if self.on_config_updated:
                self.on_config_updated(self.config)

    def _on_custom_hotkey_submitted(self):
        val = self.custom_hotkey_input.text().strip().lower()
        if val:
            self.config["hotkey"] = val
            self._save_config()
            self._update_hotkey_badges(val)
            if self.on_config_updated:
                self.on_config_updated(self.config)

    def _on_tray_toggle_changed(self, state):
        is_checked = (state == 2 or state is True)
        self.config["minimize_to_tray"] = is_checked
        self._save_config()
        if self.on_config_updated:
            self.on_config_updated(self.config)

    def _hide_to_tray(self):
        self.hide()
        if self.on_tray_notify:
            self.on_tray_notify("DIL DIL Running in Background", "Press your hotkey anywhere to dictate.")

    def _save_onboarding_key(self):
        key = self.onboarding_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "API Key Required", "Please enter your Gemini API key to proceed.")
            return

        self.config["gemini_api_key"] = key
        self._save_config()
        self.dashboard_key_input.setText(key)
        if self.on_config_updated:
            self.on_config_updated(self.config)

        self.stack.setCurrentIndex(1)
        QMessageBox.information(self, "Setup Complete", "Gemini API key saved! You can now hold your hotkey to dictate.")

    def _save_dashboard_key(self):
        key = self.dashboard_key_input.text().strip()
        self.config["gemini_api_key"] = key
        self._save_config()
        if self.on_config_updated:
            self.on_config_updated(self.config)
        QMessageBox.information(self, "Updated", "API key successfully updated!")

    def _on_language_changed(self):
        lang = self.lang_combo.currentData()
        self.config["target_language"] = lang
        self._save_config()
        if self.on_config_updated:
            self.on_config_updated(self.config)

    def _save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _on_close_clicked(self):
        if self.on_quit:
            self.on_quit()
        else:
            self.close()

    def closeEvent(self, event):
        if self.config.get("minimize_to_tray", True):
            event.ignore()
            self._hide_to_tray()
        else:
            if self.on_quit:
                self.on_quit()
            event.accept()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.config.get("minimize_to_tray", True):
                event.ignore()
                QTimer.singleShot(0, self._hide_to_tray)
                return
            elif not self.isMinimized():
                self.update()
                self.repaint()
        super().changeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.update()

    def update_active_model_badge(self, model_name: str):
        # Model updates silently in background without cluttering UI
        pass
