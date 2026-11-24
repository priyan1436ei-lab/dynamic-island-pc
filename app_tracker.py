import ctypes
import os
import psutil

user32 = ctypes.windll.user32

APP_ICONS = {
    "chrome.exe": ("🌐", "Google Chrome"),
    "msedge.exe": ("🌐", "Microsoft Edge"),
    "firefox.exe": ("🦊", "Firefox"),
    "code.exe": ("💻", "Visual Studio Code"),
    "devenv.exe": ("💻", "Visual Studio"),
    "pycharm64.exe": ("💻", "PyCharm"),
    "idea64.exe": ("💻", "IntelliJ IDEA"),
    "explorer.exe": ("📁", "கோப்புகள் (Explorer)"),
    "notepad.exe": ("📝", "நோட்பேட் (Notepad)"),
    "wordpad.exe": ("📝", "WordPad"),
    "winword.exe": ("📄", "MS Word"),
    "excel.exe": ("📊", "MS Excel"),
    "powerpnt.exe": ("📽️", "PowerPoint"),
    "spotify.exe": ("🎵", "Spotify"),
    "vlc.exe": ("🎬", "VLC Media Player"),
    "wmplayer.exe": ("🎵", "Windows Media Player"),
    "taskmgr.exe": ("⚙️", "டாஸ்க் மேனேஜர்"),
    "cmd.exe": ("⬛", "கட்டளைத் திரை (CMD)"),
    "powershell.exe": ("🟦", "PowerShell"),
    "windowsterminal.exe": ("💻", "Windows Terminal"),
    "calc.exe": ("🧮", "கால்குலேட்டர்"),
    "calculatorapp.exe": ("🧮", "கால்குலேட்டர்"),
    "discord.exe": ("💬", "Discord"),
    "telegram.exe": ("✈️", "Telegram"),
    "slack.exe": ("💬", "Slack"),
    "steam.exe": ("🎮", "Steam"),
}

class AppTracker:
    _cached_app = {
        "icon": "💻",
        "app_name": "Windows",
        "window_title": "டெஸ்க்டாப்",
        "proc_name": "explorer.exe"
    }

    @classmethod
    def get_active_app(cls):
        try:
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return cls._cached_app

            # Window Title
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()

            # Process Name
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                try:
                    proc = psutil.Process(pid.value)
                    proc_name = proc.name().lower()
                except Exception:
                    proc_name = "system"
            else:
                proc_name = "system"

            if proc_name in APP_ICONS:
                icon, app_name = APP_ICONS[proc_name]
            else:
                icon = "🪟"
                app_name = proc_name.replace(".exe", "").capitalize()

            if not title:
                title = app_name

            cls._cached_app = {
                "icon": icon,
                "app_name": app_name,
                "window_title": title,
                "proc_name": proc_name
            }
        except Exception:
            pass

        return cls._cached_app
