import time
import psutil

class SystemMonitor:
    _last_net_time = 0
    _last_bytes_sent = 0
    _last_bytes_recv = 0
    _cached_net_speed = {"upload_str": "0 KB/s", "download_str": "0 KB/s"}

    @classmethod
    def get_net_speed(cls):
        now = time.time()
        try:
            net_io = psutil.net_io_counters()
            if cls._last_net_time > 0 and (now - cls._last_net_time) >= 0.8:
                dt = now - cls._last_net_time
                up_speed = (net_io.bytes_sent - cls._last_bytes_sent) / dt
                down_speed = (net_io.bytes_recv - cls._last_bytes_recv) / dt

                cls._cached_net_speed["upload_str"] = cls._format_speed(up_speed)
                cls._cached_net_speed["download_str"] = cls._format_speed(down_speed)

                cls._last_net_time = now
                cls._last_bytes_sent = net_io.bytes_sent
                cls._last_bytes_recv = net_io.bytes_recv
            elif cls._last_net_time == 0:
                cls._last_net_time = now
                cls._last_bytes_sent = net_io.bytes_sent
                cls._last_bytes_recv = net_io.bytes_recv
        except Exception:
            pass

        return cls._cached_net_speed

    @staticmethod
    def _format_speed(bytes_per_sec):
        if bytes_per_sec < 1024:
            return f"{int(bytes_per_sec)} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"

    @classmethod
    def get_stats(cls):
        stats = {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "has_battery": False,
            "battery_percent": 100,
            "battery_plugged": True,
            "battery_time_left": None,
            "disk_percent": 0.0,
            "net_down": "0 KB/s",
            "net_up": "0 KB/s"
        }
        try:
            stats["cpu_percent"] = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            stats["ram_percent"] = mem.percent
            stats["ram_used_gb"] = round(mem.used / (1024 ** 3), 1)
            stats["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)

            battery = psutil.sensors_battery()
            if battery is not None:
                stats["has_battery"] = True
                stats["battery_percent"] = int(battery.percent)
                stats["battery_plugged"] = bool(battery.power_plugged)
                if battery.secsleft > 0:
                    mins = battery.secsleft // 60
                    stats["battery_time_left"] = f"{mins // 60}h {mins % 60}m"
            else:
                stats["has_battery"] = False
                stats["battery_percent"] = 100
                stats["battery_plugged"] = True

            disk = psutil.disk_usage('/')
            stats["disk_percent"] = disk.percent

            net = cls.get_net_speed()
            stats["net_down"] = net["download_str"]
            stats["net_up"] = net["upload_str"]
        except Exception as e:
            print(f"Monitor error: {e}")

        return stats
