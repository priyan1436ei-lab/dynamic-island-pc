import json
import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "island_settings.json")

DEFAULT_CONFIG = {
    "compact_width": 280,
    "compact_height": 38,
    "expanded_width": 560,
    "expanded_height": 330,
    "top_offset": 8,
    "corner_radius": 20,
    "expand_on_hover": True,
    "auto_collapse": True,
    "collapse_delay_ms": 1500,
    "show_clock": True,
    "clock_24h": True,
    "show_active_app": True,
    "liquid_glass_glow": True,
    "accent_color": "#007AFF",
    "quick_note": "Dynamic Island for Windows - குறிப்புகள் தட்டச்சு செய்யலாம்",
    "pomodoro_work_mins": 25,
    "pomodoro_break_mins": 5
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception as e:
            print(f"Config load error: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config_dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False
