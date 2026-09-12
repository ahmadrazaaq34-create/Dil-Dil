# 🌐 DIL DIL Cross-Platform Porting Guide (macOS & Linux)
### *Convert DIL DIL to macOS or Linux in Minutes with Any AI Assistant*

**DIL DIL (دل دل)** was originally engineered for **Windows 10 & 11** to leverage native Win32 kernel calls for sub-millisecond hotkey response, low-latency audio capture, and clipboard preservation.

However, **over 95% of the codebase** (PyQt6 UI, Google Gemini Flash streaming engine, PyAudio recording, Voice Activity Detection, and networking) is **already 100% platform-independent**. 

This guide explains what needs to be adapted for **macOS** and **Linux**, and provides a **Ready-to-Use AI Prompt** you can feed into **ChatGPT, Claude, Gemini, or Antigravity** to automatically convert the repository for your operating system.

---

## 🧭 Architecture & Platform Dependency Matrix

| Component | File | Windows Implementation | macOS Target | Linux Target |
| :--- | :--- | :--- | :--- | :--- |
| **GUI & Floating Pill** | `ui/` | PyQt6 (Cross-platform) | ✅ No changes needed | ✅ No changes needed |
| **AI Streaming Engine** | `core/gemini_engine.py` | Google GenAI SDK | ✅ No changes needed | ✅ No changes needed |
| **Audio Capture & VAD** | `core/recorder.py` | PyAudio / Wave | ✅ No changes needed | ✅ No changes needed |
| **Network Accelerator** | `core/network.py` | Python `socket` | ✅ No changes needed | ✅ No changes needed |
| **Push-to-Talk Hotkey** | `core/hotkey.py` | Win32 `GetAsyncKeyState` + `pynput` | Use pure `pynput` or Quartz EventTap | Use `pynput` (X11) or DBus Global Shortcuts (Wayland) |
| **Auto-Pasting / Typer** | `core/typer.py` | Win32 `SendInput` (`Ctrl+V`) | `pynput` / AppleScript (`Cmd+V`) | `pynput` / `xdotool` (`Ctrl+V`) |
| **Single Instance Lock** | `main.py` | Win32 Named Mutex & `user32` | Standard file lock (`fcntl`) or `QLocalServer` | Standard file lock (`fcntl`) or `QLocalServer` |
| **Memory Trimming** | `main.py` | `psapi.EmptyWorkingSet` | Handled natively by macOS Mach kernel | Handled natively by Linux kernel |

---

## 🛠️ Step-by-Step Porting Instructions

### 1. `core/hotkey.py`
On Windows, `core/hotkey.py` uses `ctypes.windll.user32.GetAsyncKeyState` as a hardware polling layer. 
For **macOS** and **Linux**:
- Remove the `ctypes.windll.user32` imports.
- Rely solely on `pynput.keyboard.Listener` (or `pynput.keyboard.GlobalHotKeys`).
- **macOS Note**: The terminal running Python must be granted **Accessibility** and **Input Monitoring** permissions in *System Settings ➔ Privacy & Security*.
- **Linux Note**: Under X11, `pynput` works out of the box. Under Wayland, configure a custom global shortcut in your desktop environment (GNOME/KDE) to trigger a socket/signal, or use `pynput` with appropriate `/dev/uinput` permissions.

### 2. `core/typer.py`
On Windows, text is injected by synthesizing `Ctrl + V` and checking foreground window HWNDs.
For **macOS**:
- Replace `Ctrl + V` with `Cmd + V`:
  ```python
  from pynput.keyboard import Controller, Key
  keyboard_ctrl = Controller()

  # Copy text to clipboard
  pyperclip.copy(text)

  # Simulate Cmd + V
  with keyboard_ctrl.pressed(Key.cmd):
      keyboard_ctrl.press('v')
      keyboard_ctrl.release('v')
  ```
- Or invoke native macOS AppleScript:
  ```python
  import subprocess
  subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])
  ```

For **Linux**:
- Keep `Ctrl + V` (or `Shift + Insert`):
  ```bash
  # Ensure xclip or wl-clipboard is installed
  sudo apt install xclip      # X11
  sudo apt install wl-clipboard # Wayland
  ```
- Trigger paste via `pynput` or `xdotool`:
  ```python
  import subprocess
  subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
  ```

### 3. `main.py`
On Windows, `main.py` uses `CreateMutexW` to prevent duplicate instances and `EmptyWorkingSet` to trim RAM.
For **macOS & Linux**:
- Replace the Windows mutex with standard cross-platform POSIX file locking:
  ```python
  import fcntl

  def acquire_lock():
      lock_file = open("/tmp/dil_dil.lock", "w")
      try:
          fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
          return lock_file
      except IOError:
          print("Another instance of DIL DIL is already running.")
          sys.exit(0)
  ```
- Remove `ensure_default_desktop()`, `trim_memory_working_set()`, and Win32 `user32` restoration calls.

---

## 🤖 Instant AI Chatbot Prompt (Copy & Paste)

If you are on a Mac or Linux machine and want your AI coding assistant (**Claude, ChatGPT, Gemini, Cursor, or Antigravity**) to convert this repository automatically, copy and paste the prompt below:

```text
I am running on [macOS / Linux]. I have cloned the open-source DIL DIL voice typing repository (https://github.com/ahmadrazaaq34-create/Dil-Dil).

The project is currently written for Windows and uses Win32 APIs in three specific files:
1. `core/hotkey.py`: Uses `ctypes.windll.user32.GetAsyncKeyState`. Please adapt this to use pure `pynput` for cross-platform hotkey detection.
2. `core/typer.py`: Uses Windows `user32.SendInput` / `keybd_event` for `Ctrl + V` and Windows clipboard history exclusion formats. Please adapt this for my OS:
   - If macOS: Use `Cmd + V` via `pynput.keyboard.Controller` or AppleScript, using `pyperclip` for clipboard management.
   - If Linux: Use `xclip`/`wl-clipboard` and simulate `Ctrl + V` via `pynput` or `xdotool`.
3. `main.py`: Uses Win32 Named Mutex (`CreateMutexW`), `psapi.EmptyWorkingSet`, and `user32` window restoration. Please replace this with cross-platform POSIX file locking (`fcntl` or `QLocalServer`), and remove the Windows desktop/memory trimmer functions.

Please make surgical modifications to these 3 files while preserving the exact PyQt6 UI design, Gemini Flash streaming logic, push-to-talk experience, and progressive sentence pasting.
```

---

## 🇵🇰 Credits & Open Source
- **Author**: Ahmed Raza ([@ahmadrazaaq34-create](https://github.com/ahmadrazaaq34-create))
- **Original Repository**: [ahmadrazaaq34-create/Dil-Dil](https://github.com/ahmadrazaaq34-create/Dil-Dil)
- **License**: MIT License
