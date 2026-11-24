import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk

from config import load_config, save_config, DEFAULT_CONFIG
from system_monitor import SystemMonitor
from media_controls import MediaControls
from weather_service import WeatherService

TRANSPARENT_KEY = "#010101"

COLOR_BG = "#0c0c10"
COLOR_CARD = "#14141a"
COLOR_CARD_BORDER = "#252530"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#8E8E93"
COLOR_SUCCESS = "#30D158"
COLOR_DANGER = "#FF453A"
COLOR_WARNING = "#FF9F0A"
COLOR_ACCENT = "#007AFF"

THEME_COLORS = {
    "நீலம் (Blue)": "#007AFF",
    "பச்சை (Green)": "#30D158",
    "ஊதா (Purple)": "#AF52DE",
    "ஆரஞ்சு (Orange)": "#FF9500",
    "சிவப்பு (Red)": "#FF2D55"
}

class DynamicIslandApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.accent_color = self.config.get("accent_color", "#007AFF")
        self.is_expanded = False
        self.animating = False
        self.current_tab = 0

        # Stopwatch state
        self.sw_running = False
        self.sw_seconds = 0

        # Pomodoro state (Work: 25m, Break: 5m)
        self.pomo_running = False
        self.pomo_is_break = False
        self.pomo_seconds_left = self.config.get("pomodoro_work_mins", 25) * 60

        # Clipboard tracking
        self.last_clipboard_text = ""
        self.clipboard_history = []

        # Equalizer animation state
        self.eq_phase = 0
        self.collapse_timer_id = None

        # Fixed transparent viewport bounds (No OS window resizing = zero shutter)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        self.viewport_w = 800
        self.viewport_h = 380
        self.viewport_x = (self.screen_width - self.viewport_w) // 2
        self.viewport_y = self.config.get("top_offset", 6)

        # Setup frameless transparent window
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        self.root.config(bg=TRANSPARENT_KEY)
        self.root.geometry(f"{self.viewport_w}x{self.viewport_h}+{self.viewport_x}+{self.viewport_y}")

        # Current dimensions for smooth vector morphing
        self.cur_w = float(self.config.get("compact_width", 260))
        self.cur_h = float(self.config.get("compact_height", 38))
        self.target_w = self.cur_w
        self.target_h = self.cur_h

        # Canvas for zero-flicker vector graphics
        self.canvas = tk.Canvas(
            self.root,
            width=self.viewport_w,
            height=self.viewport_h,
            bg=TRANSPARENT_KEY,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.show_context_menu)

        # Inner Content Frame for expanded view
        self.content_frame = tk.Frame(self.canvas, bg=COLOR_BG)
        self.content_window_id = None

        # Build UI tabs & context menu
        self.build_expanded_ui()
        self.build_context_menu()

        # Initial render
        self.redraw_island()

        # Periodic update timers
        self.update_periodic_data()
        self.check_clipboard()
        self.animate_equalizer()

    # ==========================================
    # VECTOR DRAWING (ZERO FLICKER)
    # ==========================================
    def draw_rounded_pill(self, x1, y1, x2, y2, radius, fill_color, border_color):
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        r2 = radius * 2

        self.canvas.create_arc(x1, y1, x1 + r2, y1 + r2, start=90, extent=90, fill=fill_color, outline=border_color, width=1, tags="pill_shape")
        self.canvas.create_arc(x2 - r2, y1, x2, y1 + r2, start=0, extent=90, fill=fill_color, outline=border_color, width=1, tags="pill_shape")
        self.canvas.create_arc(x2 - r2, y2 - r2, x2, y2, start=270, extent=90, fill=fill_color, outline=border_color, width=1, tags="pill_shape")
        self.canvas.create_arc(x1, y2 - r2, x1 + r2, y2, start=180, extent=90, fill=fill_color, outline=border_color, width=1, tags="pill_shape")

        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill_color, outline="", tags="pill_shape")
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill_color, outline="", tags="pill_shape")

        self.canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=border_color, width=1, tags="pill_shape")
        self.canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=border_color, width=1, tags="pill_shape")
        self.canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=border_color, width=1, tags="pill_shape")
        self.canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=border_color, width=1, tags="pill_shape")

    def get_island_bounds(self):
        cx = self.viewport_w // 2
        w = int(self.cur_w)
        h = int(self.cur_h)
        x1 = cx - w // 2
        y1 = 2
        x2 = cx + w // 2
        y2 = y1 + h
        return x1, y1, x2, y2

    def redraw_island(self):
        self.canvas.delete("pill_shape")
        self.canvas.delete("compact_element")

        x1, y1, x2, y2 = self.get_island_bounds()
        h = y2 - y1

        if not self.is_expanded:
            radius = h // 2
            self.draw_rounded_pill(x1, y1, x2, y2, radius, COLOR_BG, COLOR_CARD_BORDER)
            self.draw_compact_view(x1, y1, x2, y2)
            if self.content_window_id:
                self.canvas.itemconfigure(self.content_window_id, state="hidden")
        else:
            radius = 20
            self.draw_rounded_pill(x1, y1, x2, y2, radius, COLOR_BG, COLOR_CARD_BORDER)
            if self.content_window_id:
                pad_x = 8
                pad_y = 6
                cw = max(10, (x2 - x1) - (pad_x * 2))
                ch = max(10, (y2 - y1) - (pad_y * 2))
                self.canvas.coords(self.content_window_id, x1 + pad_x, y1 + pad_y)
                self.content_frame.config(width=cw, height=ch)
                self.canvas.itemconfigure(self.content_window_id, state="normal")

    def draw_compact_view(self, x1, y1, x2, y2):
        cy = (y1 + y2) // 2
        cx = (x1 + x2) // 2

        # 1. Left: Clock
        fmt = "%H:%M" if self.config.get("clock_24h", True) else "%I:%M %p"
        now_str = datetime.datetime.now().strftime(fmt)
        self.canvas.create_text(
            x1 + 16, cy,
            text=now_str,
            fill=COLOR_TEXT_PRIMARY,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            tags="compact_element"
        )

        # 2. Center: Dynamic Activity Equalizer / Blue Notch Dot
        dot_color = self.accent_color
        self.canvas.create_oval(
            cx - 16, cy - 3,
            cx - 10, cy + 3,
            fill=dot_color,
            outline="",
            tags="compact_element"
        )

        cpu = int(SystemMonitor.get_stats()["cpu_percent"])
        down_speed = SystemMonitor.get_stats()["net_down"]
        self.canvas.create_text(
            cx - 4, cy,
            text=f"CPU {cpu}% | ⬇️{down_speed}",
            fill=COLOR_TEXT_SECONDARY,
            font=("Segoe UI", 7, "bold"),
            anchor="w",
            tags="compact_element"
        )

        # 3. Right: Battery
        stats = SystemMonitor.get_stats()
        bat = stats["battery_percent"]
        plugged = stats["battery_plugged"]
        icon = "⚡" if plugged else "🔋"
        col = COLOR_SUCCESS if (bat > 20 or plugged) else COLOR_DANGER

        self.canvas.create_text(
            x2 - 14, cy,
            text=f"{icon} {bat}%",
            fill=col,
            font=("Segoe UI", 8, "bold"),
            anchor="e",
            tags="compact_element"
        )

    # ==========================================
    # EXPANDED TABS UI
    # ==========================================
    def build_expanded_ui(self):
        # Header bar
        self.header_frame = tk.Frame(self.content_frame, bg=COLOR_BG)
        self.header_frame.pack(fill="x", padx=4, pady=(2, 4))

        title_lbl = tk.Label(
            self.header_frame,
            text="🏝️ Dynamic Island Pro",
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG,
            font=("Segoe UI", 9, "bold")
        )
        title_lbl.pack(side="left", padx=4)

        btn_collapse = tk.Button(
            self.header_frame,
            text="▲ சுருக்கு",
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD,
            activeforeground=COLOR_TEXT_PRIMARY,
            activebackground="#2a2a34",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=6, pady=1,
            command=self.collapse_island
        )
        btn_collapse.pack(side="right", padx=2)

        # Navigation Tabs
        self.tab_bar = tk.Frame(self.header_frame, bg=COLOR_BG)
        self.tab_bar.pack(side="right", padx=4)

        self.tab_buttons = []
        tabs_info = [
            ("📊 சிஸ்டம்", 0),
            ("🎵 மீடியா", 1),
            ("⚡ கருவிகள்", 2),
            ("📋 குறிப்பு", 3),
            ("🚀 துவக்கி", 4),
            ("⚙️ அமைப்புகள்", 5)
        ]

        for title, idx in tabs_info:
            b = tk.Button(
                self.tab_bar,
                text=title,
                fg=COLOR_TEXT_SECONDARY,
                bg=COLOR_CARD,
                activeforeground=COLOR_TEXT_PRIMARY,
                activebackground=self.accent_color,
                relief="flat",
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
                padx=5, pady=2,
                command=lambda i=idx: self.switch_tab(i)
            )
            b.pack(side="left", padx=1)
            self.tab_buttons.append(b)

        # Pages Container
        self.pages_container = tk.Frame(self.content_frame, bg=COLOR_CARD, bd=1, relief="flat")
        self.pages_container.pack(fill="both", expand=True, padx=4, pady=2)

        self.page_system = self.build_tab_system(self.pages_container)
        self.page_media = self.build_tab_media(self.pages_container)
        self.page_tools = self.build_tab_tools(self.pages_container)
        self.page_notes = self.build_tab_notes(self.pages_container)
        self.page_launcher = self.build_tab_launcher(self.pages_container)
        self.page_settings = self.build_tab_settings(self.pages_container)

        self.pages = [
            self.page_system, self.page_media, self.page_tools,
            self.page_notes, self.page_launcher, self.page_settings
        ]

        x1, y1, _, _ = self.get_island_bounds()
        self.content_window_id = self.canvas.create_window(
            x1 + 8, y1 + 6,
            window=self.content_frame,
            anchor="nw",
            state="hidden"
        )
        self.switch_tab(0)

    def switch_tab(self, index):
        self.current_tab = index
        for i, page in enumerate(self.pages):
            if i == index:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()

        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.config(bg=self.accent_color, fg=COLOR_TEXT_PRIMARY)
            else:
                btn.config(bg=COLOR_CARD, fg=COLOR_TEXT_SECONDARY)

    # 1. System Tab with Real-time Network Monitor
    def build_tab_system(self, parent):
        page = tk.Frame(parent, bg=COLOR_CARD, padx=12, pady=6)

        # CPU Row
        cpu_box = tk.Frame(page, bg=COLOR_CARD)
        cpu_box.pack(fill="x", pady=2)
        self.lbl_cpu = tk.Label(cpu_box, text="CPU சுமை: 0%", fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"), width=16, anchor="w")
        self.lbl_cpu.pack(side="left")
        self.bar_cpu = ttk.Progressbar(cpu_box, orient="horizontal", mode="determinate", length=220)
        self.bar_cpu.pack(side="left", fill="x", expand=True, padx=4)

        # RAM Row
        ram_box = tk.Frame(page, bg=COLOR_CARD)
        ram_box.pack(fill="x", pady=2)
        self.lbl_ram = tk.Label(ram_box, text="RAM பயன்பாடு: 0%", fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"), width=16, anchor="w")
        self.lbl_ram.pack(side="left")
        self.bar_ram = ttk.Progressbar(ram_box, orient="horizontal", mode="determinate", length=220)
        self.bar_ram.pack(side="left", fill="x", expand=True, padx=4)

        # Network IO Speed Row
        net_box = tk.Frame(page, bg=COLOR_CARD)
        net_box.pack(fill="x", pady=4)
        self.lbl_net_down = tk.Label(net_box, text="⬇️ பதிவிறக்கம் (Down): 0 KB/s", fg=COLOR_SUCCESS, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        self.lbl_net_down.pack(side="left")
        self.lbl_net_up = tk.Label(net_box, text="⬆️ பதிவேற்றம் (Up): 0 KB/s", fg=COLOR_ACCENT, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        self.lbl_net_up.pack(side="right")

        # Battery & Disk
        status_box = tk.Frame(page, bg=COLOR_CARD)
        status_box.pack(fill="x", pady=4)
        self.lbl_battery = tk.Label(status_box, text="🔋 பேட்டரி: 100% (சார்ஜிங்)", fg=COLOR_SUCCESS, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        self.lbl_battery.pack(side="left")
        self.lbl_disk = tk.Label(status_box, text="💾 வட்டு (C:): 0%", fg=COLOR_WARNING, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        self.lbl_disk.pack(side="right")

        return page

    # 2. Media Controls Tab with Animated Visualizer
    def build_tab_media(self, parent):
        page = tk.Frame(parent, bg=COLOR_CARD, padx=12, pady=6)

        info = tk.Label(page, text="🎵 விண்டோஸ் மீடியா & ஒலி அளவுக் கட்டுப்பாடு", fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, font=("Segoe UI", 8))
        info.pack(pady=2)

        # Equalizer Visualizer Canvas
        self.eq_canvas = tk.Canvas(page, width=280, height=24, bg=COLOR_CARD, highlightthickness=0)
        self.eq_canvas.pack(pady=4)

        ctrl_box = tk.Frame(page, bg=COLOR_CARD)
        ctrl_box.pack(pady=4)

        btn_prev = tk.Button(ctrl_box, text="⏮ முந்தையது", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=3, command=MediaControls.prev_track)
        btn_prev.pack(side="left", padx=4)

        self.btn_play = tk.Button(ctrl_box, text="⏯ இயக்கு / நிறுத்து", bg=self.accent_color, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=12, pady=3, command=MediaControls.play_pause)
        self.btn_play.pack(side="left", padx=4)

        btn_next = tk.Button(ctrl_box, text="⏭ அடுத்தது", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=3, command=MediaControls.next_track)
        btn_next.pack(side="left", padx=4)

        vol_box = tk.Frame(page, bg=COLOR_CARD)
        vol_box.pack(pady=4)

        btn_vdown = tk.Button(vol_box, text="🔉 சத்தம் குறை", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=MediaControls.volume_down)
        btn_vdown.pack(side="left", padx=3)

        btn_mute = tk.Button(vol_box, text="🔇 மௌனம்", bg="#202028", fg=COLOR_DANGER, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=MediaControls.volume_mute)
        btn_mute.pack(side="left", padx=3)

        btn_vup = tk.Button(vol_box, text="🔊 சத்தம் கூட்டு", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=MediaControls.volume_up)
        btn_vup.pack(side="left", padx=3)

        return page

    def animate_equalizer(self):
        if hasattr(self, 'eq_canvas') and self.current_tab == 1 and self.is_expanded:
            self.eq_canvas.delete("all")
            self.eq_phase = (self.eq_phase + 1) % 10
            import math
            for i in range(18):
                h = int(6 + 8 * (math.sin(self.eq_phase + i * 0.6) + 1))
                x = 10 + i * 15
                self.eq_canvas.create_rectangle(x, 24 - h, x + 8, 24, fill=self.accent_color, outline="")
        self.root.after(100, self.animate_equalizer)

    # 3. Tools Tab with Stopwatch & Pomodoro Timer
    def build_tab_tools(self, parent):
        page = tk.Frame(parent, bg=COLOR_CARD, padx=12, pady=6)

        # Stopwatch Section
        sw_box = tk.Frame(page, bg=COLOR_CARD)
        sw_box.pack(fill="x", pady=2)

        self.lbl_stopwatch = tk.Label(sw_box, text="⏱️ 00:00:00", fg=self.accent_color, bg=COLOR_CARD, font=("Segoe UI", 12, "bold"), width=12, anchor="w")
        self.lbl_stopwatch.pack(side="left")

        self.btn_sw = tk.Button(sw_box, text="துவக்கு (Start)", bg=COLOR_SUCCESS, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=self.toggle_stopwatch)
        self.btn_sw.pack(side="left", padx=3)

        btn_sw_reset = tk.Button(sw_box, text="மீட்டமை (Reset)", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=self.reset_stopwatch)
        btn_sw_reset.pack(side="left", padx=3)

        # Pomodoro Section
        pomo_box = tk.Frame(page, bg=COLOR_CARD)
        pomo_box.pack(fill="x", pady=4)

        self.lbl_pomo = tk.Label(pomo_box, text="🍅 போக்கஸ்: 25:00", fg=COLOR_WARNING, bg=COLOR_CARD, font=("Segoe UI", 11, "bold"), width=16, anchor="w")
        self.lbl_pomo.pack(side="left")

        self.btn_pomo = tk.Button(pomo_box, text="போக்கஸ் துவக்கு", bg=COLOR_WARNING, fg="#000000", font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=self.toggle_pomodoro)
        self.btn_pomo.pack(side="left", padx=3)

        btn_pomo_reset = tk.Button(pomo_box, text="மீட்டமை", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=self.reset_pomodoro)
        btn_pomo_reset.pack(side="left", padx=3)

        # Shortcuts
        act_box = tk.Frame(page, bg=COLOR_CARD)
        act_box.pack(fill="x", pady=4)

        btn_screen = tk.Button(act_box, text="📸 ஸ்கிரீன்ஷாட் (Screenshot)", bg="#202028", fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=3, command=MediaControls.take_screenshot)
        btn_screen.pack(side="left", padx=4)

        btn_lock = tk.Button(act_box, text="🔒 கணினியைப் பூட்டு (Lock PC)", bg="#202028", fg=COLOR_DANGER, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=3, command=MediaControls.lock_workstation)
        btn_lock.pack(side="left", padx=4)

        return page

    def toggle_stopwatch(self):
        if self.sw_running:
            self.sw_running = False
            self.btn_sw.config(text="தொடங்கு (Resume)", bg=COLOR_SUCCESS)
        else:
            self.sw_running = True
            self.btn_sw.config(text="நிறுத்து (Pause)", bg=COLOR_DANGER)
            self.run_stopwatch_tick()

    def reset_stopwatch(self):
        self.sw_running = False
        self.sw_seconds = 0
        self.lbl_stopwatch.config(text="⏱️ 00:00:00")
        self.btn_sw.config(text="துவக்கு (Start)", bg=COLOR_SUCCESS)

    def run_stopwatch_tick(self):
        if self.sw_running:
            self.sw_seconds += 1
            hrs = self.sw_seconds // 3600
            mins = (self.sw_seconds % 3600) // 60
            secs = self.sw_seconds % 60
            self.lbl_stopwatch.config(text=f"⏱️ {hrs:02d}:{mins:02d}:{secs:02d}")
            self.root.after(1000, self.run_stopwatch_tick)

    def toggle_pomodoro(self):
        if self.pomo_running:
            self.pomo_running = False
            self.btn_pomo.config(text="தொடங்கு (Resume)", bg=COLOR_WARNING)
        else:
            self.pomo_running = True
            self.btn_pomo.config(text="நிறுத்து (Pause)", bg=COLOR_DANGER)
            self.run_pomodoro_tick()

    def reset_pomodoro(self):
        self.pomo_running = False
        self.pomo_is_break = False
        self.pomo_seconds_left = self.config.get("pomodoro_work_mins", 25) * 60
        self.lbl_pomo.config(text="🍅 போக்கஸ்: 25:00", fg=COLOR_WARNING)
        self.btn_pomo.config(text="போக்கஸ் துவக்கு", bg=COLOR_WARNING)

    def run_pomodoro_tick(self):
        if self.pomo_running:
            if self.pomo_seconds_left > 0:
                self.pomo_seconds_left -= 1
                mins = self.pomo_seconds_left // 60
                secs = self.pomo_seconds_left % 60
                tag = "☕ இடைவேளை" if self.pomo_is_break else "🍅 போக்கஸ்"
                col = COLOR_SUCCESS if self.pomo_is_break else COLOR_WARNING
                self.lbl_pomo.config(text=f"{tag}: {mins:02d}:{secs:02d}", fg=col)
                self.root.after(1000, self.run_pomodoro_tick)
            else:
                self.pomo_is_break = not self.pomo_is_break
                duration = self.config.get("pomodoro_break_mins", 5) if self.pomo_is_break else self.config.get("pomodoro_work_mins", 25)
                self.pomo_seconds_left = duration * 60
                tag = "☕ இடைவேளை நேரம்!" if self.pomo_is_break else "🍅 போக்கஸ் நேரம்!"
                self.lbl_pomo.config(text=tag)
                self.run_pomodoro_tick()

    # 4. Clipboard History & Quick Notes Tab
    def build_tab_notes(self, parent):
        page = tk.Frame(parent, bg=COLOR_CARD, padx=8, pady=4)

        # Top: Clipboard History
        lbl_clip = tk.Label(page, text="📋 கிளிப்போர்டு வரலாறு (கடைசியாக நகலெடுக்கப்பட்டவை):", fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        lbl_clip.pack(anchor="w")

        self.clip_frame = tk.Frame(page, bg=COLOR_CARD)
        self.clip_frame.pack(fill="x", pady=2)
        self.render_clipboard_items()

        # Bottom: Quick Notes Text Area
        lbl_notes = tk.Label(page, text="📝 விரைவுக் குறிப்புகள் (Scratchpad):", fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        lbl_notes.pack(anchor="w", pady=(4, 2))

        self.txt_notes = tk.Text(page, bg="#181820", fg=COLOR_TEXT_PRIMARY, insertbackground=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8), relief="flat", bd=1, height=4)
        self.txt_notes.insert("1.0", self.config.get("quick_note", ""))
        self.txt_notes.pack(fill="both", expand=True)
        self.txt_notes.bind("<KeyRelease>", self.on_notes_changed)

        return page

    def check_clipboard(self):
        try:
            text = self.root.clipboard_get().strip()
            if text and text != self.last_clipboard_text and len(text) > 0:
                self.last_clipboard_text = text
                if text not in self.clipboard_history:
                    self.clipboard_history.insert(0, text)
                    if len(self.clipboard_history) > 4:
                        self.clipboard_history.pop()
                    if hasattr(self, 'clip_frame'):
                        self.render_clipboard_items()
        except Exception:
            pass
        self.root.after(1500, self.check_clipboard)

    def render_clipboard_items(self):
        for widget in self.clip_frame.winfo_children():
            widget.destroy()

        if not self.clipboard_history:
            empty_lbl = tk.Label(self.clip_frame, text="நகலெடுக்கப்பட்ட உரை ஏதுமில்லை.", fg="#636366", bg=COLOR_CARD, font=("Segoe UI", 7))
            empty_lbl.pack(anchor="w")
            return

        for item in self.clipboard_history[:3]:
            row = tk.Frame(self.clip_frame, bg="#1c1c24")
            row.pack(fill="x", pady=1)

            display_txt = item.replace("\n", " ")[:36] + ("..." if len(item) > 36 else "")
            txt_lbl = tk.Label(row, text=display_txt, fg=COLOR_TEXT_PRIMARY, bg="#1c1c24", font=("Segoe UI", 7))
            txt_lbl.pack(side="left", padx=4)

            btn_copy = tk.Button(row, text="📋 மீண்டும் நகலெடு", bg=self.accent_color, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 6, "bold"), relief="flat", cursor="hand2", padx=4, command=lambda t=item: self.copy_to_clip(t))
            btn_copy.pack(side="right", padx=2)

    def copy_to_clip(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def on_notes_changed(self, event=None):
        self.config["quick_note"] = self.txt_notes.get("1.0", "end-1c")
        save_config(self.config)

    # 5. Launcher & Weather Tab
    def build_tab_launcher(self, parent):
        page = tk.Frame(parent, bg=COLOR_CARD, padx=12, pady=6)

        # Weather Section
        self.lbl_weather = tk.Label(page, text="வானிலை: தகவல்களைப் பெறுகிறது...", fg=COLOR_WARNING, bg=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        self.lbl_weather.pack(pady=4)

        lbl_apps = tk.Label(page, text="🚀 ஒரு கிளிக்கில் அப்ளிகேஷனைத் திறக்க:", fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"))
        lbl_apps.pack(pady=(4, 6))

        apps_grid = tk.Frame(page, bg=COLOR_CARD)
        apps_grid.pack(pady=4)

        btn_style = {"bg": "#202028", "fg": COLOR_TEXT_PRIMARY, "font": ("Segoe UI", 8, "bold"), "relief": "flat", "cursor": "hand2", "padx": 8, "pady": 4}

        btn_calc = tk.Button(apps_grid, text="🧮 கால்குலேட்டர்", command=MediaControls.launch_calc, **btn_style)
        btn_calc.grid(row=0, column=0, padx=4, pady=3)

        btn_notes = tk.Button(apps_grid, text="📝 நோட்பேட்", command=MediaControls.launch_notepad, **btn_style)
        btn_notes.grid(row=0, column=1, padx=4, pady=3)

        btn_files = tk.Button(apps_grid, text="📁 எக்ஸ்ப்ளோரர்", command=MediaControls.launch_explorer, **btn_style)
        btn_files.grid(row=0, column=2, padx=4, pady=3)

        btn_task = tk.Button(apps_grid, text="⚙️ டாஸ்க் மேனேஜர்", command=MediaControls.launch_taskmgr, **btn_style)
        btn_task.grid(row=1, column=0, padx=4, pady=3)

        btn_web = tk.Button(apps_grid, text="🌐 பிரவுசர் (Web)", command=MediaControls.launch_browser, **btn_style)
        btn_web.grid(row=1, column=1, padx=4, pady=3)

        return page

    # 6. Settings Tab (Customizable Size, Themes & Width)
    def build_tab_settings(self, parent):
        page = tk.Frame(parent, bg=COLOR_CARD, padx=10, pady=4)

        # Compact Width
        f_cw = tk.Frame(page, bg=COLOR_CARD)
        f_cw.pack(fill="x", pady=1)
        self.lbl_set_cw = tk.Label(f_cw, text=f"சுருங்கிய அகலம் (Width): {int(self.cur_w)}px", fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"), width=26, anchor="w")
        self.lbl_set_cw.pack(side="left")
        self.scale_cw = tk.Scale(f_cw, from_=160, to=380, orient="horizontal", showvalue=0, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, highlightthickness=0, troughcolor="#202028", activebackground=self.accent_color, command=self.on_set_compact_width)
        self.scale_cw.set(self.config['compact_width'])
        self.scale_cw.pack(side="left", fill="x", expand=True, padx=4)

        # Compact Height
        f_ch = tk.Frame(page, bg=COLOR_CARD)
        f_ch.pack(fill="x", pady=1)
        self.lbl_set_ch = tk.Label(f_ch, text=f"சுருங்கிய உயரம் (Height): {self.config['compact_height']}px", fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"), width=26, anchor="w")
        self.lbl_set_ch.pack(side="left")
        self.scale_ch = tk.Scale(f_ch, from_=26, to=50, orient="horizontal", showvalue=0, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, highlightthickness=0, troughcolor="#202028", activebackground=self.accent_color, command=self.on_set_compact_height)
        self.scale_ch.set(self.config['compact_height'])
        self.scale_ch.pack(side="left", fill="x", expand=True, padx=4)

        # Expanded Width
        f_ew = tk.Frame(page, bg=COLOR_CARD)
        f_ew.pack(fill="x", pady=1)
        self.lbl_set_ew = tk.Label(f_ew, text=f"விரிந்த அகலம் (Exp Width): {self.config['expanded_width']}px", fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"), width=26, anchor="w")
        self.lbl_set_ew.pack(side="left")
        self.scale_ew = tk.Scale(f_ew, from_=400, to=740, orient="horizontal", showvalue=0, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, highlightthickness=0, troughcolor="#202028", activebackground=self.accent_color, command=self.on_set_expanded_width)
        self.scale_ew.set(self.config['expanded_width'])
        self.scale_ew.pack(side="left", fill="x", expand=True, padx=4)

        # Top Margin
        f_top = tk.Frame(page, bg=COLOR_CARD)
        f_top.pack(fill="x", pady=1)
        self.lbl_set_top = tk.Label(f_top, text=f"மேல் இடைவெளி (Margin): {self.config['top_offset']}px", fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, font=("Segoe UI", 8, "bold"), width=26, anchor="w")
        self.lbl_set_top.pack(side="left")
        self.scale_top = tk.Scale(f_top, from_=0, to=40, orient="horizontal", showvalue=0, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, highlightthickness=0, troughcolor="#202028", activebackground=self.accent_color, command=self.on_set_top_offset)
        self.scale_top.set(self.config['top_offset'])
        self.scale_top.pack(side="left", fill="x", expand=True, padx=4)

        # Theme Colors & 24h Clock
        f_opts = tk.Frame(page, bg=COLOR_CARD)
        f_opts.pack(fill="x", pady=2)

        lbl_theme = tk.Label(f_opts, text="தீம் வண்ணம்:", fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, font=("Segoe UI", 8))
        lbl_theme.pack(side="left")

        for name, hex_col in THEME_COLORS.items():
            btn_col = tk.Button(f_opts, bg=hex_col, width=2, height=1, relief="flat", cursor="hand2", command=lambda c=hex_col: self.set_accent_color(c))
            btn_col.pack(side="left", padx=2)

        self.var_24h = tk.BooleanVar(value=self.config.get("clock_24h", True))
        chk_24h = tk.Checkbutton(f_opts, text="24-மணி நேர வடிவம்", variable=self.var_24h, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, selectcolor="#202028", font=("Segoe UI", 8), command=self.on_chk_24h_changed)
        chk_24h.pack(side="right", padx=2)

        # Checkboxes
        f_chk = tk.Frame(page, bg=COLOR_CARD)
        f_chk.pack(fill="x", pady=2)

        self.var_hover = tk.BooleanVar(value=self.config.get("expand_on_hover", True))
        chk_h = tk.Checkbutton(f_chk, text="மவுஸ் சென்றதும் விரிவடை", variable=self.var_hover, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, selectcolor="#202028", font=("Segoe UI", 8), command=self.on_chk_hover_changed)
        chk_h.pack(side="left", padx=2)

        self.var_auto = tk.BooleanVar(value=self.config.get("auto_collapse", True))
        chk_a = tk.Checkbutton(f_chk, text="தானாக சுருங்கு", variable=self.var_auto, fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, selectcolor="#202028", font=("Segoe UI", 8), command=self.on_chk_auto_changed)
        chk_a.pack(side="left", padx=6)

        # Action Buttons
        f_btns = tk.Frame(page, bg=COLOR_CARD)
        f_btns.pack(fill="x", pady=2)

        btn_reset = tk.Button(f_btns, text="இயல்பு நிலை", bg="#202028", fg=COLOR_DANGER, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=8, pady=2, command=self.reset_defaults)
        btn_reset.pack(side="left")

        btn_save = tk.Button(f_btns, text="💾 அமைப்புகளைச் சேமி", bg=COLOR_SUCCESS, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", padx=12, pady=2, command=self.save_settings)
        btn_save.pack(side="right")

        return page

    def set_accent_color(self, hex_code):
        self.accent_color = hex_code
        self.config["accent_color"] = hex_code
        save_config(self.config)
        self.btn_play.config(bg=hex_code)
        self.switch_tab(self.current_tab)
        self.redraw_island()

    def on_chk_24h_changed(self):
        self.config["clock_24h"] = self.var_24h.get()
        save_config(self.config)
        self.redraw_island()

    def on_set_compact_width(self, val):
        val = int(val)
        self.config["compact_width"] = val
        self.lbl_set_cw.config(text=f"சுருங்கிய அகலம் (Width): {val}px")
        if not self.is_expanded and not self.animating:
            self.cur_w = val
            self.target_w = val
            self.redraw_island()

    def on_set_compact_height(self, val):
        val = int(val)
        self.config["compact_height"] = val
        self.lbl_set_ch.config(text=f"சுருங்கிய உயரம் (Height): {val}px")
        if not self.is_expanded and not self.animating:
            self.cur_h = val
            self.target_h = val
            self.redraw_island()

    def on_set_expanded_width(self, val):
        val = int(val)
        self.config["expanded_width"] = val
        self.lbl_set_ew.config(text=f"விரிந்த அகலம் (Exp Width): {val}px")
        if self.is_expanded and not self.animating:
            self.cur_w = val
            self.target_w = val
            self.redraw_island()

    def on_set_top_offset(self, val):
        val = int(val)
        self.config["top_offset"] = val
        self.lbl_set_top.config(text=f"மேல் இடைவெளி (Margin): {val}px")
        self.viewport_y = val
        self.root.geometry(f"{self.viewport_w}x{self.viewport_h}+{self.viewport_x}+{self.viewport_y}")

    def on_chk_hover_changed(self):
        self.config["expand_on_hover"] = self.var_hover.get()

    def on_chk_auto_changed(self):
        self.config["auto_collapse"] = self.var_auto.get()

    def reset_defaults(self):
        self.config = DEFAULT_CONFIG.copy()
        save_config(self.config)
        self.scale_cw.set(self.config['compact_width'])
        self.scale_ch.set(self.config['compact_height'])
        self.scale_ew.set(self.config['expanded_width'])
        self.scale_top.set(self.config['top_offset'])
        self.var_hover.set(self.config['expand_on_hover'])
        self.var_auto.set(self.config['auto_collapse'])
        self.accent_color = self.config['accent_color']
        if not self.is_expanded:
            self.cur_w = self.config['compact_width']
            self.cur_h = self.config['compact_height']
        else:
            self.cur_w = self.config['expanded_width']
            self.cur_h = self.config['expanded_height']
        self.redraw_island()

    def save_settings(self):
        save_config(self.config)
        self.collapse_island()

    # ==========================================
    # FLUID 60FPS VECTOR ANIMATION
    # ==========================================
    def expand_island(self):
        if not self.is_expanded and not self.animating:
            self.is_expanded = True
            self.target_w = float(self.config.get("expanded_width", 540))
            self.target_h = float(self.config.get("expanded_height", 320))
            self.animate_step()

    def collapse_island(self):
        if self.is_expanded and not self.animating:
            self.is_expanded = False
            self.target_w = float(self.config.get("compact_width", 260))
            self.target_h = float(self.config.get("compact_height", 38))
            if self.content_window_id:
                self.canvas.itemconfigure(self.content_window_id, state="hidden")
            self.animate_step()

    def toggle_island(self):
        if self.is_expanded:
            self.collapse_island()
        else:
            self.expand_island()

    def animate_step(self):
        self.animating = True
        diff_w = self.target_w - self.cur_w
        diff_h = self.target_h - self.cur_h

        if abs(diff_w) < 3.0 and abs(diff_h) < 3.0:
            self.cur_w = self.target_w
            self.cur_h = self.target_h
            self.animating = False
            self.redraw_island()
            return

        step = 0.32
        self.cur_w += diff_w * step
        self.cur_h += diff_h * step

        self.redraw_island()
        self.root.after(16, self.animate_step)

    # ==========================================
    # MOUSE HIT TESTING
    # ==========================================
    def is_pointer_inside_island(self, x, y):
        x1, y1, x2, y2 = self.get_island_bounds()
        return (x1 <= x <= x2 and y1 <= y <= y2)

    def on_canvas_motion(self, event):
        if self.is_pointer_inside_island(event.x, event.y):
            if self.collapse_timer_id:
                self.root.after_cancel(self.collapse_timer_id)
                self.collapse_timer_id = None
            if self.config.get("expand_on_hover", True) and not self.is_expanded and not self.animating:
                self.expand_island()
        else:
            if self.config.get("auto_collapse", True) and self.is_expanded and not self.animating and not self.collapse_timer_id:
                delay = self.config.get("collapse_delay_ms", 1200)
                self.collapse_timer_id = self.root.after(delay, self.collapse_island)

    def on_canvas_leave(self, event):
        if self.config.get("auto_collapse", True) and self.is_expanded and not self.animating:
            delay = self.config.get("collapse_delay_ms", 1200)
            if not self.collapse_timer_id:
                self.collapse_timer_id = self.root.after(delay, self.collapse_island)

    def on_canvas_click(self, event):
        if self.is_pointer_inside_island(event.x, event.y):
            if not self.is_expanded:
                self.expand_island()

    def build_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0, bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, activebackground=self.accent_color, activeforeground=COLOR_TEXT_PRIMARY)
        self.menu.add_command(label="🏝️ Dynamic Island Pro", state="disabled")
        self.menu.add_separator()
        self.menu.add_command(label="விரி / சுருக்கு (Toggle Expand)", command=self.toggle_island)
        self.menu.add_command(label="⚙️ அமைப்புகள் (Settings)", command=self.open_settings)
        self.menu.add_separator()
        self.menu.add_command(label="❌ வெளியேறு (Exit)", command=self.root.destroy)

    def open_settings(self):
        self.expand_island()
        self.switch_tab(5)

    def show_context_menu(self, event):
        if self.is_pointer_inside_island(event.x, event.y):
            self.menu.post(event.x_root, event.y_root)

    # ==========================================
    # PERIODIC UPDATES
    # ==========================================
    def update_periodic_data(self):
        stats = SystemMonitor.get_stats()
        cpu = int(stats["cpu_percent"])
        ram = int(stats["ram_percent"])
        bat = stats["battery_percent"]
        plugged = stats["battery_plugged"]

        self.lbl_cpu.config(text=f"CPU சுமை: {cpu}%")
        self.bar_cpu["value"] = cpu

        ram_used = stats["ram_used_gb"]
        ram_total = stats["ram_total_gb"]
        self.lbl_ram.config(text=f"RAM பயன்பாடு: {ram}% ({ram_used} GB / {ram_total} GB)")
        self.bar_ram["value"] = ram

        self.lbl_net_down.config(text=f"⬇️ பதிவிறக்கம்: {stats['net_down']}")
        self.lbl_net_up.config(text=f"⬆️ பதிவேற்றம்: {stats['net_up']}")

        bat_icon = "⚡" if plugged else "🔋"
        chg_text = "மின் இணைப்பு (Charging)" if plugged else "மின்கலம் (Battery)"
        self.lbl_battery.config(text=f"{bat_icon} பேட்டரி: {bat}% - {chg_text}")
        self.lbl_disk.config(text=f"💾 வட்டு (C:): {stats['disk_percent']}%")

        # Weather update
        if hasattr(self, 'lbl_weather'):
            self.lbl_weather.config(text=WeatherService.get_weather())

        if not self.is_expanded and not self.animating:
            x1, y1, x2, y2 = self.get_island_bounds()
            self.canvas.delete("compact_element")
            self.draw_compact_view(x1, y1, x2, y2)

        self.root.after(1000, self.update_periodic_data)
