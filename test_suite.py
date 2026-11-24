import unittest
import os
import sys
import tkinter as tk

from config import load_config, save_config, DEFAULT_CONFIG
from system_monitor import SystemMonitor
from weather_service import WeatherService
from media_controls import MediaControls
from app_tracker import AppTracker
from dynamic_island import DynamicIslandApp

class ComprehensiveTestSuite(unittest.TestCase):
    def test_01_config_robustness(self):
        print("Testing Config Loading & Persistence...")
        cfg = load_config()
        self.assertIn("compact_width", cfg)
        self.assertIn("expanded_width", cfg)
        self.assertIn("accent_color", cfg)
        self.assertIn("show_active_app", cfg)
        self.assertIn("liquid_glass_glow", cfg)

        # Test mutation and persistence
        cfg["test_key"] = "test_val_123"
        self.assertTrue(save_config(cfg))
        cfg_reloaded = load_config()
        self.assertEqual(cfg_reloaded.get("test_key"), "test_val_123")

    def test_02_system_and_network_monitor(self):
        print("Testing System Stats & Real-time Network IO...")
        stats = SystemMonitor.get_stats()
        self.assertIn("cpu_percent", stats)
        self.assertIn("ram_percent", stats)
        self.assertIn("net_down", stats)
        self.assertIn("net_up", stats)
        self.assertIsInstance(stats["net_down"], str)
        self.assertIsInstance(stats["net_up"], str)
        print(f"Stats: CPU={stats['cpu_percent']}%, RAM={stats['ram_percent']}%, Down={stats['net_down']}, Up={stats['net_up']}")

    def test_03_active_app_tracker(self):
        print("Testing Windows Active App & Window Tracking...")
        app_info = AppTracker.get_active_app()
        self.assertIn("icon", app_info)
        self.assertIn("app_name", app_info)
        self.assertIn("window_title", app_info)
        self.assertIn("proc_name", app_info)
        print(f"Active App Detected: {app_info['icon']} {app_info['app_name']} ({app_info['window_title']})")

    def test_04_weather_service(self):
        print("Testing Weather Service with Cache...")
        weather = WeatherService.get_weather()
        self.assertIsInstance(weather, str)
        self.assertTrue(len(weather) > 0)
        print(f"Weather: {weather}")

    def test_05_media_and_launchers(self):
        print("Testing Media Key Simulation & App Launchers...")
        self.assertTrue(callable(MediaControls.play_pause))
        self.assertTrue(callable(MediaControls.volume_up))
        self.assertTrue(callable(MediaControls.volume_down))
        self.assertTrue(callable(MediaControls.volume_mute))
        self.assertTrue(callable(MediaControls.launch_calc))
        self.assertTrue(callable(MediaControls.launch_notepad))
        self.assertTrue(callable(MediaControls.launch_explorer))
        self.assertTrue(callable(MediaControls.launch_taskmgr))
        self.assertTrue(callable(MediaControls.launch_browser))

    def test_06_liquid_glass_ui_and_alerts(self):
        print("Testing Dynamic Island Liquid Glass UI, All 6 Tabs & Dynamic Alerts...")
        root = tk.Tk()
        app = DynamicIslandApp(root)
        root.update()

        # Check initial state
        self.assertFalse(app.is_expanded)

        # Test Tab switching across all 6 tabs
        for idx in range(6):
            app.switch_tab(idx)
            root.update()
            self.assertEqual(app.current_tab, idx)

        # Test Dynamic Alert Notification banner
        app.show_dynamic_alert("🔔", "சோதனை அறிவிப்பு", "இது ஒரு சோதனை அறிவிப்பு", duration_ms=500)
        self.assertTrue(app.alert_active)
        root.update()

        app.dismiss_alert()
        self.assertFalse(app.alert_active)
        root.update()

        # Test expand / collapse
        app.expand_island()
        for _ in range(12):
            root.update()
        self.assertTrue(app.is_expanded)

        # Test Settings changes
        app.on_set_compact_width(290)
        app.on_set_compact_height(40)
        app.on_set_expanded_width(580)
        app.set_accent_color("#AF52DE")
        root.update()
        self.assertEqual(app.accent_color, "#AF52DE")

        app.collapse_island()
        for _ in range(12):
            root.update()
        self.assertFalse(app.is_expanded)

        # Test Stopwatch & Pomodoro
        app.toggle_stopwatch()
        self.assertTrue(app.sw_running)
        app.reset_stopwatch()
        self.assertFalse(app.sw_running)

        app.toggle_pomodoro()
        self.assertTrue(app.pomo_running)
        app.reset_pomodoro()
        self.assertFalse(app.pomo_running)

        root.destroy()
        print("All UI and lifecycle tests passed successfully!")

if __name__ == "__main__":
    unittest.main()
