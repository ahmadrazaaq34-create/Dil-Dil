import os
import json
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class SettingsDialog(QDialog):
    def __init__(self, config_path: str, on_save_callback=None, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.on_save_callback = on_save_callback
        self.config = self._load_config()

        self.setWindowTitle("Wispr Flow Settings")
        self.setFixedSize(460, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #a855f7;
            }
            QPushButton {
                background-color: #a855f7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #9333ea;
            }
            QPushButton#secondaryBtn {
                background-color: #334155;
                color: #e2e8f0;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #475569;
            }
            QPushButton#linkBtn {
                background: transparent;
                color: #38bdf8;
                text-decoration: underline;
                border: none;
                padding: 0;
                text-align: left;
                font-size: 12px;
            }
        """)

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
            "hotkey": "ctrl+space",
            "mode": "urdu_to_english"
        }

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title header
        title = QLabel("🎙️ Wispr Flow Voice Assistant")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        subtitle = QLabel("Hold your hotkey, speak in Urdu, and get instant English typing.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(subtitle)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1e293b;")
        layout.addWidget(line)

        # Gemini API Key Field
        key_label = QLabel("Google Gemini API Key:")
        layout.addWidget(key_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your Gemini API key (AQ... or AIza...)")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setText(self.config.get("gemini_api_key", ""))
        layout.addWidget(self.key_input)

        # API link button
        link_btn = QPushButton("👉 Get your Free Gemini API Key from Google AI Studio")
        link_btn.setObjectName("linkBtn")
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        layout.addWidget(link_btn)

        # Mode Selection
        mode_label = QLabel("Voice Translation Mode:")
        layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Urdu / Hindi to Fluent English (Recommended)", "urdu_to_english")
        self.mode_combo.addItem("Direct English (Grammar Polish)", "direct_english")
        self.mode_combo.addItem("Verbatim (Exact Speech-to-Text)", "verbatim")

        current_mode = self.config.get("mode", "urdu_to_english")
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == current_mode:
                self.mode_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.mode_combo)

        # Push-to-Talk Hotkey display
        hotkey_label = QLabel(f"Push-to-Talk Hotkey: <b>Ctrl + Space</b> (Hold to record)")
        hotkey_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(hotkey_label)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        test_btn = QPushButton("Test API Key")
        test_btn.setObjectName("secondaryBtn")
        test_btn.clicked.connect(self._test_api_key)

        save_btn = QPushButton("Save & Close")
        save_btn.clicked.connect(self._save_settings)

        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _test_api_key(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "API Key Missing", "Please enter a Gemini API key first.")
            return

        try:
            from google import genai
            client = genai.Client(api_key=key)
            res = client.models.generate_content(model="gemini-3.6-flash", contents="Hi")
            QMessageBox.information(self, "Success", "API Key is valid and connected to Gemini!")
        except Exception as e:
            QMessageBox.critical(self, "API Key Error", f"Failed to verify key: {e}")

    def _save_settings(self):
        self.config["gemini_api_key"] = self.key_input.text().strip()
        self.config["mode"] = self.mode_combo.currentData()

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            if self.on_save_callback:
                self.on_save_callback(self.config)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save config: {e}")
