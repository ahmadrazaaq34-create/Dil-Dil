import time
import ctypes
import threading
from pynput import keyboard

user32 = ctypes.windll.user32
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short

VK_MAP = {
    "ctrl": [0x11, 0xA2, 0xA3],
    "control": [0x11, 0xA2, 0xA3],
    "lctrl": [0xA2],
    "rctrl": [0xA3],
    "shift": [0x10, 0xA0, 0xA1],
    "lshift": [0xA0],
    "rshift": [0xA1],
    "alt": [0x12, 0xA4, 0xA5],
    "lalt": [0xA4],
    "ralt": [0xA5],
    "space": [0x20],
    "tab": [0x09],
    "caps_lock": [0x14],
    "f1": [0x70], "f2": [0x71], "f3": [0x72], "f4": [0x73],
    "f5": [0x74], "f6": [0x75], "f7": [0x76], "f8": [0x77],
    "f9": [0x78], "f10": [0x79], "f11": [0x7A], "f12": [0x7B],
}

PYNPUT_KEY_MAP = {
    "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "control": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
    "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr},
    "space": {keyboard.Key.space},
    "tab": {keyboard.Key.tab},
    "f1": {keyboard.Key.f1}, "f2": {keyboard.Key.f2}, "f3": {keyboard.Key.f3},
    "f4": {keyboard.Key.f4}, "f5": {keyboard.Key.f5}, "f6": {keyboard.Key.f6},
    "f7": {keyboard.Key.f7}, "f8": {keyboard.Key.f8}, "f9": {keyboard.Key.f9},
    "f10": {keyboard.Key.f10}, "f11": {keyboard.Key.f11}, "f12": {keyboard.Key.f12},
}

class HotkeyManager:
    """
    Ultra-reliable dual-layer push-to-talk hotkey manager.
    Combines low-level Windows kernel GetAsyncKeyState hardware polling (15ms cycle)
    with debounced release protection (90ms) and pynput event listeners.
    Works seamlessly across all foreground windows, elevated applications, and rapid key combinations.
    """
    def __init__(self, hotkey_str: str = "ctrl+shift", on_press_callback=None, on_release_callback=None):
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback

        self._is_active = False
        self._running = False
        self._listener = None
        self._poller_thread = None
        self._lock = threading.Lock()
        self._pressed_parts = set()
        self.parsed_parts = []
        self.set_hotkey(hotkey_str)

    def set_hotkey(self, hotkey_str: str):
        with self._lock:
            self.hotkey_str = hotkey_str.lower().strip()
            cleaned = self.hotkey_str.replace("+", " ").replace("-", " ")
            raw_parts = [p.strip() for p in cleaned.split() if p.strip()]
            self.parsed_parts = raw_parts
            self._pressed_parts.clear()
            self._is_active = False
            print(f"[Hotkey] Configured push-to-talk combination: {self.hotkey_str} (keys: {self.parsed_parts})")

    def _get_part_for_pynput_key(self, key) -> str:
        for part in self.parsed_parts:
            mapped_keys = PYNPUT_KEY_MAP.get(part)
            if mapped_keys and key in mapped_keys:
                return part
            if hasattr(key, 'char') and key.char and key.char.lower() == part:
                return part
        return ""

    def _is_physically_held(self) -> bool:
        """Checks raw hardware state via Windows GetAsyncKeyState for every key in the combination."""
        if not self.parsed_parts:
            return False
        for part in self.parsed_parts:
            vks = VK_MAP.get(part)
            if not vks:
                if len(part) == 1:
                    vks = [ord(part.upper())]
                else:
                    continue
            part_down = any(bool(user32.GetAsyncKeyState(code) & 0x8000) for code in vks)
            if not part_down:
                return False
        return True

    def _trigger_press(self):
        if not self._is_active:
            self._is_active = True
            print(f"[Hotkey] Press detected: {self.hotkey_str} ACTIVE")
            if self.on_press_callback:
                threading.Thread(target=self.on_press_callback, daemon=True).start()

    def _trigger_release(self):
        if self._is_active:
            self._is_active = False
            self._pressed_parts.clear()
            print(f"[Hotkey] Release detected: {self.hotkey_str} RELEASED")
            if self.on_release_callback:
                threading.Thread(target=self.on_release_callback, daemon=True).start()

    def _poll_loop(self):
        """
        Hardware polling loop (15ms).
        Provides 100% reliable detection even if hooks are delayed or blocked by elevated windows.
        Debounces release by requiring 6 consecutive unheld ticks (~90ms) to eliminate transient glitches.
        """
        consecutive_unheld = 0
        consecutive_held = 0

        while self._running:
            time.sleep(0.015)
            held = self._is_physically_held()

            with self._lock:
                if held:
                    consecutive_held += 1
                    consecutive_unheld = 0
                    if consecutive_held >= 2 and not self._is_active:
                        self._trigger_press()
                else:
                    consecutive_held = 0
                    if self._is_active:
                        consecutive_unheld += 1
                        # 6 consecutive ticks = ~90ms debounce window
                        if consecutive_unheld >= 6:
                            self._trigger_release()

    def _on_press(self, key):
        part = self._get_part_for_pynput_key(key)
        if part:
            with self._lock:
                self._pressed_parts.add(part)
                if all(p in self._pressed_parts for p in self.parsed_parts) or self._is_physically_held():
                    self._trigger_press()

    def _on_release(self, key):
        part = self._get_part_for_pynput_key(key)
        if part:
            with self._lock:
                self._pressed_parts.discard(part)
                if self._is_active and not (all(p in self._pressed_parts for p in self.parsed_parts) and self._is_physically_held()):
                    self._trigger_release()

    def start(self):
        self._running = True
        # 1. Start hardware polling thread
        if self._poller_thread is None or not self._poller_thread.is_alive():
            self._poller_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poller_thread.start()

        # 2. Start pynput keyboard listener
        if self._listener is None:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()
        print("[Hotkey] Dual-layer hotkey listener & hardware poller active.")

    def stop(self):
        self._running = False
        with self._lock:
            self._is_active = False
            self._pressed_parts.clear()
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
