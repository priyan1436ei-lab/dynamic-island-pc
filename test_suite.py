import unittest
import os
import sys
import tkinter as tk

from config import load_config, save_config, DEFAULT_CONFIG
from system_monitor import SystemMonitor
from weather_service import WeatherService
from media_controls import MediaControls
from dynamic_island import DynamicIslandApp

class TestDynamicIsland(unittest.TestCase):
    def test_01_config(self):
        print("Testing Config...")
        cfg = load_config()
        self.assertIn("compact_width", cfg)
        self.assertIn("expanded_width", cfg)
        self.assertIn("accent_color", cfg)
        
        cfg["test_key"] = "test_val"
        save_result = save_config(cfg)
        self.assertTrue(save_result)
        
        cfg2 = load_config()
        self.assertEqual(cfg2.get("test_key"), "test_val")

    def test_02_system_monitor(self):
        print("Testing System Monitor & Network IO...")
        stats = SystemMonitor.get_stats()
        self.assertIn("cpu_percent", stats)
        self.assertIn("ram_percent", stats)
        self.assertIn("battery_percent", stats)
        self.assertIn("net_down", stats)
        self.assertIn("net_up", stats)
        print(f"Stats OK: CPU {stats['cpu_percent']}%, RAM {stats['ram_percent']}%, Net: Down {stats['net_down']}, Up {stats['net_up']}")

    def test_03_weather_service(self):
        print("Testing Weather Service...")
        weather = WeatherService.get_weather()
        self.assertIsInstance(weather, str)
        self.assertTrue(len(weather) > 0)
        print(f"Weather OK: {weather}")

    def test_04_media_controls(self):
        print("Testing Media & Launcher definitions...")
        self.assertTrue(callable(MediaControls.play_pause))
        self.assertTrue(callable(MediaControls.volume_up))
        self.assertTrue(callable(MediaControls.launch_calc))
        self.assertTrue(callable(MediaControls.launch_notepad))

    def test_05_dynamic_island_ui_lifecycle(self):
        print("Testing DynamicIslandApp UI, all 6 tabs, animations and events...")
        root = tk.Tk()
        app = DynamicIslandApp(root)
        root.update()

        # Test initial compact state
        self.assertFalse(app.is_expanded)

        # Test tab switching across all 6 tabs
        for tab_idx in range(6):
            app.switch_tab(tab_idx)
            root.update()
            self.assertEqual(app.current_tab, tab_idx)

        # Test expand animation
        app.expand_island()
        for _ in range(15):
            root.update()
        self.assertTrue(app.is_expanded)

        # Test settings change live
        app.on_set_compact_width(280)
        app.on_set_compact_height(40)
        app.on_set_expanded_width(560)
        app.set_accent_color("#30D158")
        root.update()
        self.assertEqual(app.config["compact_width"], 280)
        self.assertEqual(app.accent_color, "#30D158")

        # Test collapse animation
        app.collapse_island()
        for _ in range(15):
            root.update()
        self.assertFalse(app.is_expanded)

        # Test stopwatch & pomodoro timers
        app.toggle_stopwatch()
        self.assertTrue(app.sw_running)
        app.reset_stopwatch()
        self.assertFalse(app.sw_running)

        app.toggle_pomodoro()
        self.assertTrue(app.pomo_running)
        app.reset_pomodoro()
        self.assertFalse(app.pomo_running)

        # Test clipboard copy & notes
        app.copy_to_clip("Dynamic Island Test Clip")
        root.update()
        self.assertEqual(root.clipboard_get(), "Dynamic Island Test Clip")

        root.destroy()
        print("All UI lifecycle tests passed with flying colors!")

if __name__ == "__main__":
    unittest.main()
