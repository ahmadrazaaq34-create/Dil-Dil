import os
import win32com.client

wscript = win32com.client.Dispatch("WScript.Shell")
desktop = os.path.expanduser("~/Desktop")
old_shortcut = os.path.join(desktop, "Wispr Flow.lnk")
if os.path.exists(old_shortcut):
    try:
        os.remove(old_shortcut)
    except Exception:
        pass

shortcut_path = os.path.join(desktop, "DIL DIL.lnk")
target_py = r"C:\Users\PMLS\AppData\Local\Programs\Python\Python312\pythonw.exe"
main_script = os.path.abspath("main.py")
working_dir = os.path.dirname(main_script)
icon_path = os.path.join(working_dir, "assets", "app_icon.ico")

shortcut = wscript.CreateShortcut(shortcut_path)
shortcut.TargetPath = target_py
shortcut.Arguments = f'"{main_script}"'
shortcut.WorkingDirectory = working_dir
shortcut.IconLocation = f"{icon_path},0"
shortcut.Description = "DIL DIL: AI Voice Dictation Assistant"
shortcut.Save()

print("SUCCESS: Shortcut created at:", shortcut_path)

