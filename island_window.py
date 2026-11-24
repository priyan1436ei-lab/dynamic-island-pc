import os
import sys
import datetime
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QIcon, QPainterPath, QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QSlider, QCheckBox, QTextEdit, QProgressBar,
    QFrame, QGraphicsDropShadowEffect, QApplication
)

from config import load_config, save_config, DEFAULT_CONFIG
from system_monitor import SystemMonitor
from media_controls import MediaControls

class DynamicIslandWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.is_expanded = False
        self.system_stats = SystemMonitor.get_stats()
        
        # Stopwatch state
        self.stopwatch_running = False
        self.stopwatch_seconds = 0

        # Setup frameless transparent window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        # Main animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)

        # Hover collapse timer
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(self.auto_collapse_check)

        # System stats update timer (every 1 second)
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(1000)
        self.stats_timer.timeout.connect(self.update_system_data)
        self.stats_timer.start()

        # Stopwatch timer
        self.sw_timer = QTimer(self)
        self.sw_timer.setInterval(1000)
        self.sw_timer.timeout.connect(self.update_stopwatch)

        # Init UI
        self.init_ui()
        self.apply_geometry(expanded=False, animate=False)

    def init_ui(self):
        # Outer container layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Pill Container widget (handles background drawing)
        self.container = QWidget(self)
        self.container.setObjectName("IslandContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 4, 12, 6)
        self.container_layout.setSpacing(4)
        self.main_layout.addWidget(self.container)

        # Stacked widget for switching between Compact View and Expanded View
        self.stack = QStackedWidget(self.container)
        self.container_layout.addWidget(self.stack)

        # Build Compact & Expanded views
        self.build_compact_view()
        self.build_expanded_view()

        self.stack.setCurrentIndex(0) # Start in compact mode

    # ==========================
    # COMPACT VIEW
    # ==========================
    def build_compact_view(self):
        self.compact_widget = QWidget()
        compact_layout = QHBoxLayout(self.compact_widget)
        compact_layout.setContentsMargins(6, 2, 6, 2)
        compact_layout.setSpacing(8)

        # Left item: Clock / Indicator
        self.compact_clock_label = QLabel("00:00")
        self.compact_clock_label.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 13px; font-family: 'Segoe UI', sans-serif;")
        compact_layout.addWidget(self.compact_clock_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Middle item: Animated dynamic notch dot
        self.compact_center_dot = QLabel("●")
        self.compact_center_dot.setStyleSheet("color: #007AFF; font-size: 10px;")
        compact_layout.addWidget(self.compact_center_dot, alignment=Qt.AlignmentFlag.AlignCenter)

        # Center indicator text (CPU or Music wave)
        self.compact_status_label = QLabel("CPU 0%")
        self.compact_status_label.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: 500;")
        compact_layout.addWidget(self.compact_status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        compact_layout.addStretch()

        # Right item: Battery / Status
        self.compact_battery_label = QLabel("⚡ 100%")
        self.compact_battery_label.setStyleSheet("color: #30D158; font-weight: 600; font-size: 12px;")
        compact_layout.addWidget(self.compact_battery_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.stack.addWidget(self.compact_widget)

    # ==========================
    # EXPANDED VIEW
    # ==========================
    def build_expanded_view(self):
        self.expanded_widget = QWidget()
        expanded_layout = QVBoxLayout(self.expanded_widget)
        expanded_layout.setContentsMargins(8, 6, 8, 8)
        expanded_layout.setSpacing(6)

        # Top Bar (Header & Navigation Tabs)
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(4, 0, 4, 0)

        title_label = QLabel("🏝️ Dynamic Island")
        title_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
        header_bar.addWidget(title_label)

        header_bar.addStretch()

        # Navigation Buttons (Tabs)
        self.tab_buttons = []
        tabs_info = [
            ("📊 Status", 0),
            ("🎵 Media", 1),
            ("⚡ Tools", 2),
            ("📝 Note", 3),
            ("⚙️ Settings", 4)
        ]
        
        tab_bar_layout = QHBoxLayout()
        tab_bar_layout.setSpacing(4)
        for name, idx in tabs_info:
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(24)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1C1C1E;
                    color: #A1A1A6;
                    border-radius: 12px;
                    padding: 2px 10px;
                    font-size: 11px;
                    font-weight: 600;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                }
                QPushButton:hover {
                    background-color: #2C2C2E;
                    color: #FFFFFF;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self.switch_tab(i))
            tab_bar_layout.addWidget(btn)
            self.tab_buttons.append(btn)
        
        header_bar.addLayout(tab_bar_layout)

        # Collapse Button
        collapse_btn = QPushButton("▲")
        collapse_btn.setToolTip("சுருக்கு (Collapse)")
        collapse_btn.setFixedSize(22, 22)
        collapse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border-radius: 11px;
                font-size: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
        """)
        collapse_btn.clicked.connect(self.collapse_island)
        header_bar.addWidget(collapse_btn)

        expanded_layout.addLayout(header_bar)

        # Tab Content Area
        self.tabs_content = QStackedWidget()
        expanded_layout.addWidget(self.tabs_content)

        # 1. System Tab
        self.build_tab_system()
        # 2. Media Tab
        self.build_tab_media()
        # 3. Tools Tab
        self.build_tab_tools()
        # 4. Notes Tab
        self.build_tab_notes()
        # 5. Settings Tab (Size & Appearance Customization)
        self.build_tab_settings()

        self.stack.addWidget(self.expanded_widget)
        self.switch_tab(0)

    def switch_tab(self, index):
        self.tabs_content.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007AFF;
                        color: #FFFFFF;
                        border-radius: 12px;
                        padding: 2px 10px;
                        font-size: 11px;
                        font-weight: 700;
                        border: none;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1C1C1E;
                        color: #A1A1A6;
                        border-radius: 12px;
                        padding: 2px 10px;
                        font-size: 11px;
                        font-weight: 600;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                    }
                    QPushButton:hover {
                        background-color: #2C2C2E;
                        color: #FFFFFF;
                    }
                """)

    # ==========================
    # TAB 1: SYSTEM MONITOR
    # ==========================
    def build_tab_system(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # CPU Row
        cpu_row = QHBoxLayout()
        self.cpu_label = QLabel("CPU சுமை: 0%")
        self.cpu_label.setStyleSheet("color: #E5E5EA; font-size: 12px; font-weight: 600;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setFixedHeight(8)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2C2C2E;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007AFF, stop:1 #5856D6);
                border-radius: 4px;
            }
        """)
        cpu_row.addWidget(self.cpu_label)
        cpu_row.addWidget(self.cpu_bar)
        layout.addLayout(cpu_row)

        # RAM Row
        ram_row = QHBoxLayout()
        self.ram_label = QLabel("RAM பயன்பாடு: 0%")
        self.ram_label.setStyleSheet("color: #E5E5EA; font-size: 12px; font-weight: 600;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setFixedHeight(8)
        self.ram_bar.setTextVisible(False)
        self.ram_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2C2C2E;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #30D158, stop:1 #34C759);
                border-radius: 4px;
            }
        """)
        ram_row.addWidget(self.ram_label)
        ram_row.addWidget(self.ram_bar)
        layout.addLayout(ram_row)

        # Battery & Disk Row
        bottom_row = QHBoxLayout()
        self.battery_info_label = QLabel("🔋 பேட்டரி: 100% (சார்ஜிங்)")
        self.battery_info_label.setStyleSheet("color: #30D158; font-size: 12px; font-weight: 600;")
        self.disk_info_label = QLabel("💾 சேமிப்பகம் (C:): 0%")
        self.disk_info_label.setStyleSheet("color: #FF9F0A; font-size: 12px; font-weight: 600;")
        bottom_row.addWidget(self.battery_info_label)
        bottom_row.addStretch()
        bottom_row.addWidget(self.disk_info_label)
        layout.addLayout(bottom_row)

        self.tabs_content.addWidget(page)

    # ==========================
    # TAB 2: MEDIA CONTROLS
    # ==========================
    def build_tab_media(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        status_lbl = QLabel("🎵 மீடியா மற்றும் ஒலி அளவுக் கட்டுப்பாடு (Media Controls)")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_lbl.setStyleSheet("color: #A1A1A6; font-size: 12px; font-weight: 500;")
        layout.addWidget(status_lbl)

        # Media Playback Buttons
        media_buttons = QHBoxLayout()
        media_buttons.setSpacing(16)
        media_buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_prev = QPushButton("⏮ முந்தையது")
        btn_play = QPushButton("⏯ இயக்கு / நிறுத்து")
        btn_next = QPushButton("⏭ அடுத்தது")

        btn_style = """
            QPushButton {
                background-color: #242426;
                color: #FFFFFF;
                border-radius: 14px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background-color: #323236;
            }
            QPushButton:pressed {
                background-color: #007AFF;
            }
        """
        for b in [btn_prev, btn_play, btn_next]:
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet(btn_style)

        btn_prev.clicked.connect(MediaControls.prev_track)
        btn_play.clicked.connect(MediaControls.play_pause)
        btn_next.clicked.connect(MediaControls.next_track)

        media_buttons.addWidget(btn_prev)
        media_buttons.addWidget(btn_play)
        media_buttons.addWidget(btn_next)
        layout.addLayout(media_buttons)

        # Volume Controls
        vol_layout = QHBoxLayout()
        vol_layout.setSpacing(12)
        vol_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_vol_down = QPushButton("🔉 சத்தம் குறை")
        btn_mute = QPushButton("🔇 மௌனம் (Mute)")
        btn_vol_up = QPushButton("🔊 சத்தம் கூட்டு")

        for b in [btn_vol_down, btn_mute, btn_vol_up]:
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet(btn_style)

        btn_vol_down.clicked.connect(MediaControls.volume_down)
        btn_mute.clicked.connect(MediaControls.volume_mute)
        btn_vol_up.clicked.connect(MediaControls.volume_up)

        vol_layout.addWidget(btn_vol_down)
        vol_layout.addWidget(btn_mute)
        vol_layout.addWidget(btn_vol_up)
        layout.addLayout(vol_layout)

        self.tabs_content.addWidget(page)

    # ==========================
    # TAB 3: TOOLS & STOPWATCH
    # ==========================
    def build_tab_tools(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Stopwatch Section
        sw_box = QHBoxLayout()
        self.stopwatch_label = QLabel("⏱️ 00:00:00")
        self.stopwatch_label.setStyleSheet("color: #007AFF; font-size: 18px; font-weight: bold;")
        sw_box.addWidget(self.stopwatch_label)
        sw_box.addStretch()

        self.btn_sw_toggle = QPushButton("துவக்கு (Start)")
        self.btn_sw_reset = QPushButton("மீட்டமை (Reset)")

        tool_btn_style = """
            QPushButton {
                background-color: #242426;
                color: #FFFFFF;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background-color: #323236;
            }
        """
        for b in [self.btn_sw_toggle, self.btn_sw_reset]:
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet(tool_btn_style)

        self.btn_sw_toggle.clicked.connect(self.toggle_stopwatch)
        self.btn_sw_reset.clicked.connect(self.reset_stopwatch)

        sw_box.addWidget(self.btn_sw_toggle)
        sw_box.addWidget(self.btn_sw_reset)
        layout.addLayout(sw_box)

        # Quick Actions
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        btn_screenshot = QPushButton("📸 ஸ்கிரீன்ஷாட் (Screenshot)")
        btn_screenshot.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_screenshot.setStyleSheet(tool_btn_style)
        btn_screenshot.clicked.connect(MediaControls.take_screenshot)

        btn_lock = QPushButton("🔒 கணினியைப் பூட்டு (Lock PC)")
        btn_lock.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_lock.setStyleSheet(tool_btn_style)
        btn_lock.clicked.connect(MediaControls.lock_workstation)

        actions_row.addWidget(btn_screenshot)
        actions_row.addWidget(btn_lock)
        layout.addLayout(actions_row)

        self.tabs_content.addWidget(page)

    def toggle_stopwatch(self):
        if self.stopwatch_running:
            self.stopwatch_running = False
            self.sw_timer.stop()
            self.btn_sw_toggle.setText("தொடங்கு (Resume)")
            self.btn_sw_toggle.setStyleSheet("background-color: #30D158; color: #FFFFFF; border-radius: 12px; padding: 4px 12px; font-weight: 600;")
        else:
            self.stopwatch_running = True
            self.sw_timer.start()
            self.btn_sw_toggle.setText("நிறுத்து (Pause)")
            self.btn_sw_toggle.setStyleSheet("background-color: #FF453A; color: #FFFFFF; border-radius: 12px; padding: 4px 12px; font-weight: 600;")

    def reset_stopwatch(self):
        self.stopwatch_running = False
        self.sw_timer.stop()
        self.stopwatch_seconds = 0
        self.stopwatch_label.setText("⏱️ 00:00:00")
        self.btn_sw_toggle.setText("துவக்கு (Start)")
        self.btn_sw_toggle.setStyleSheet("background-color: #242426; color: #FFFFFF; border-radius: 12px; padding: 4px 12px; font-weight: 600;")

    def update_stopwatch(self):
        self.stopwatch_seconds += 1
        hrs = self.stopwatch_seconds // 3600
        mins = (self.stopwatch_seconds % 3600) // 60
        secs = self.stopwatch_seconds % 60
        self.stopwatch_label.setText(f"⏱️ {hrs:02d}:{mins:02d}:{secs:02d}")

    # ==========================
    # TAB 4: QUICK NOTES
    # ==========================
    def build_tab_notes(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(6)

        note_label = QLabel("📝 விரைவுக் குறிப்புகள் (Quick Tasks / Notes):")
        note_label.setStyleSheet("color: #E5E5EA; font-size: 11px; font-weight: 600;")
        layout.addWidget(note_label)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("இங்கு குறிப்புகளைத் தட்டச்சு செய்யலாம்...")
        self.note_edit.setText(self.config.get("quick_note", ""))
        self.note_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
        """)
        self.note_edit.textChanged.connect(self.on_note_changed)
        layout.addWidget(self.note_edit)

        self.tabs_content.addWidget(page)

    def on_note_changed(self):
        self.config["quick_note"] = self.note_edit.toPlainText()
        save_config(self.config)

    # ==========================
    # TAB 5: SETTINGS (SIZE & WIDTH CUSTOMIZATION)
    # ==========================
    def build_tab_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(6)

        slider_style = """
            QSlider::groove:horizontal {
                height: 4px;
                background: #2C2C2E;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #007AFF;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }
        """

        # 1. Compact Width (சுருங்கிய நிலை அகலம்)
        w_row = QHBoxLayout()
        self.lbl_c_width = QLabel(f"சுருங்கிய நிலை அகலம் (Width): {self.config['compact_width']}px")
        self.lbl_c_width.setStyleSheet("color: #E5E5EA; font-size: 11px;")
        self.slider_c_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_c_width.setRange(140, 420)
        self.slider_c_width.setValue(self.config['compact_width'])
        self.slider_c_width.setStyleSheet(slider_style)
        self.slider_c_width.valueChanged.connect(self.on_compact_width_change)
        w_row.addWidget(self.lbl_c_width)
        w_row.addWidget(self.slider_c_width)
        layout.addLayout(w_row)

        # 2. Compact Height (சுருங்கிய நிலை உயரம்)
        h_row = QHBoxLayout()
        self.lbl_c_height = QLabel(f"சுருங்கிய நிலை உயரம் (Height): {self.config['compact_height']}px")
        self.lbl_c_height.setStyleSheet("color: #E5E5EA; font-size: 11px;")
        self.slider_c_height = QSlider(Qt.Orientation.Horizontal)
        self.slider_c_height.setRange(26, 55)
        self.slider_c_height.setValue(self.config['compact_height'])
        self.slider_c_height.setStyleSheet(slider_style)
        self.slider_c_height.valueChanged.connect(self.on_compact_height_change)
        h_row.addWidget(self.lbl_c_height)
        h_row.addWidget(self.slider_c_height)
        layout.addLayout(h_row)

        # 3. Expanded Width (விரிந்த நிலை அகலம்)
        ew_row = QHBoxLayout()
        self.lbl_e_width = QLabel(f"விரிந்த நிலை அகலம் (Exp Width): {self.config['expanded_width']}px")
        self.lbl_e_width.setStyleSheet("color: #E5E5EA; font-size: 11px;")
        self.slider_e_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_e_width.setRange(350, 700)
        self.slider_e_width.setValue(self.config['expanded_width'])
        self.slider_e_width.setStyleSheet(slider_style)
        self.slider_e_width.valueChanged.connect(self.on_expanded_width_change)
        ew_row.addWidget(self.lbl_e_width)
        ew_row.addWidget(self.slider_e_width)
        layout.addLayout(ew_row)

        # 4. Top Margin Offset (திரையின் மேல் இருந்து இடைவெளி)
        top_row = QHBoxLayout()
        self.lbl_top = QLabel(f"மேல் இடைவெளி (Top Margin): {self.config['top_offset']}px")
        self.lbl_top.setStyleSheet("color: #E5E5EA; font-size: 11px;")
        self.slider_top = QSlider(Qt.Orientation.Horizontal)
        self.slider_top.setRange(0, 45)
        self.slider_top.setValue(self.config['top_offset'])
        self.slider_top.setStyleSheet(slider_style)
        self.slider_top.valueChanged.connect(self.on_top_offset_change)
        top_row.addWidget(self.lbl_top)
        top_row.addWidget(self.slider_top)
        layout.addLayout(top_row)

        # Checkboxes
        check_row = QHBoxLayout()
        self.chk_hover = QCheckBox("மவுஸ் சென்றதும் விரிவடை (Hover Expand)")
        self.chk_hover.setChecked(self.config.get("expand_on_hover", True))
        self.chk_hover.setStyleSheet("color: #A1A1A6; font-size: 11px;")
        self.chk_hover.stateChanged.connect(self.on_hover_check_changed)

        self.chk_auto_collapse = QCheckBox("தானாக சுருங்கு (Auto Collapse)")
        self.chk_auto_collapse.setChecked(self.config.get("auto_collapse", True))
        self.chk_auto_collapse.setStyleSheet("color: #A1A1A6; font-size: 11px;")
        self.chk_auto_collapse.stateChanged.connect(self.on_auto_collapse_changed)

        check_row.addWidget(self.chk_hover)
        check_row.addWidget(self.chk_auto_collapse)
        layout.addLayout(check_row)

        # Action Buttons: Reset & Save
        btn_row = QHBoxLayout()
        btn_reset = QPushButton("இயல்பு நிலைக்கு மீட்டமை (Reset)")
        btn_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FF453A;
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #3A3A3C; }
        """)
        btn_reset.clicked.connect(self.reset_to_defaults)

        btn_save = QPushButton("💾 அமைப்புகளைச் சேமி (Save)")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #30D158;
                color: #FFFFFF;
                border-radius: 10px;
                padding: 4px 16px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover { background-color: #34C759; }
        """)
        btn_save.clicked.connect(self.save_settings_clicked)

        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self.tabs_content.addWidget(page)

    def on_compact_width_change(self, val):
        self.config['compact_width'] = val
        self.lbl_c_width.setText(f"சுருங்கிய நிலை அகலம் (Width): {val}px")
        if not self.is_expanded:
            self.apply_geometry(expanded=False, animate=True)

    def on_compact_height_change(self, val):
        self.config['compact_height'] = val
        self.lbl_c_height.setText(f"சுருங்கிய நிலை உயரம் (Height): {val}px")
        if not self.is_expanded:
            self.apply_geometry(expanded=False, animate=True)

    def on_expanded_width_change(self, val):
        self.config['expanded_width'] = val
        self.lbl_e_width.setText(f"விரிந்த நிலை அகலம் (Exp Width): {val}px")
        if self.is_expanded:
            self.apply_geometry(expanded=True, animate=True)

    def on_top_offset_change(self, val):
        self.config['top_offset'] = val
        self.lbl_top.setText(f"மேல் இடைவெளி (Top Margin): {val}px")
        self.apply_geometry(expanded=self.is_expanded, animate=True)

    def on_hover_check_changed(self, state):
        self.config['expand_on_hover'] = (state == 2)

    def on_auto_collapse_changed(self, state):
        self.config['auto_collapse'] = (state == 2)

    def reset_to_defaults(self):
        self.config = DEFAULT_CONFIG.copy()
        save_config(self.config)
        self.slider_c_width.setValue(self.config['compact_width'])
        self.slider_c_height.setValue(self.config['compact_height'])
        self.slider_e_width.setValue(self.config['expanded_width'])
        self.slider_top.setValue(self.config['top_offset'])
        self.chk_hover.setChecked(self.config['expand_on_hover'])
        self.chk_auto_collapse.setChecked(self.config['auto_collapse'])
        self.apply_geometry(expanded=self.is_expanded, animate=True)

    def save_settings_clicked(self):
        save_config(self.config)
        self.collapse_island()

    # ==========================
    # REAL-TIME UPDATES
    # ==========================
    def update_system_data(self):
        # Update clock
        now = datetime.datetime.now()
        self.compact_clock_label.setText(now.strftime("%H:%M"))

        # Fetch stats
        self.system_stats = SystemMonitor.get_stats()
        cpu = int(self.system_stats["cpu_percent"])
        ram = int(self.system_stats["ram_percent"])
        bat = self.system_stats["battery_percent"]
        plugged = self.system_stats["battery_plugged"]

        # Compact stats
        self.compact_status_label.setText(f"CPU {cpu}%")
        bat_icon = "⚡" if plugged else "🔋"
        self.compact_battery_label.setText(f"{bat_icon} {bat}%")
        if bat <= 20 and not plugged:
            self.compact_battery_label.setStyleSheet("color: #FF453A; font-weight: 600; font-size: 12px;")
        else:
            self.compact_battery_label.setStyleSheet("color: #30D158; font-weight: 600; font-size: 12px;")

        # Expanded System stats
        self.cpu_label.setText(f"CPU சுமை: {cpu}%")
        self.cpu_bar.setValue(cpu)

        ram_used = self.system_stats["ram_used_gb"]
        ram_total = self.system_stats["ram_total_gb"]
        self.ram_label.setText(f"RAM பயன்பாடு: {ram}% ({ram_used} GB / {ram_total} GB)")
        self.ram_bar.setValue(ram)

        state_text = "மின் இணைப்பு (Charging)" if plugged else "மின்கலம் (Battery)"
        self.battery_info_label.setText(f"{bat_icon} பேட்டரி: {bat}% - {state_text}")
        disk = self.system_stats["disk_percent"]
        self.disk_info_label.setText(f"💾 வட்டு (C:): {disk}%")

    # ==========================
    # GEOMETRY & ANIMATION
    # ==========================
    def get_target_geometry(self, expanded=False):
        screen = QApplication.primaryScreen().geometry()
        top_offset = self.config.get("top_offset", 8)
        if expanded:
            w = self.config.get("expanded_width", 460)
            h = self.config.get("expanded_height", 260)
        else:
            w = self.config.get("compact_width", 220)
            h = self.config.get("compact_height", 38)

        x = screen.x() + (screen.width() - w) // 2
        y = screen.y() + top_offset
        return QRect(x, y, w, h)

    def apply_geometry(self, expanded=False, animate=True):
        target_rect = self.get_target_geometry(expanded)
        if animate:
            self.anim.stop()
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(target_rect)
            self.anim.start()
        else:
            self.setGeometry(target_rect)

    def expand_island(self):
        if not self.is_expanded:
            self.is_expanded = True
            self.stack.setCurrentIndex(1)
            self.apply_geometry(expanded=True, animate=True)

    def collapse_island(self):
        if self.is_expanded:
            self.is_expanded = False
            self.stack.setCurrentIndex(0)
            self.apply_geometry(expanded=False, animate=True)

    def toggle_island(self):
        if self.is_expanded:
            self.collapse_island()
        else:
            self.expand_island()

    # ==========================
    # MOUSE EVENTS
    # ==========================
    def enterEvent(self, event):
        self.collapse_timer.stop()
        if self.config.get("expand_on_hover", True) and not self.is_expanded:
            self.expand_island()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.config.get("auto_collapse", True) and self.is_expanded:
            delay = self.config.get("collapse_delay_ms", 1200)
            self.collapse_timer.start(delay)
        super().leaveEvent(event)

    def auto_collapse_check(self):
        # Only collapse if mouse is not currently over the widget
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.collapse_island()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_expanded:
                self.expand_island()
        super().mousePressEvent(event)

    # ==========================
    # CUSTOM PAINTING (APPLE PILL)
    # ==========================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        path = QPainterPath()

        if self.is_expanded:
            radius = 24.0
        else:
            radius = float(rect.height() / 2.0)

        path.addRoundedRect(0.5, 0.5, float(rect.width() - 1), float(rect.height() - 1), radius, radius)

        # Black body with subtle transparency
        painter.fillPath(path, QBrush(QColor(12, 12, 14, int(255 * self.config.get("opacity", 0.96)))))

        # Outer delicate glowing border
        border_pen = QPen(QColor(255, 255, 255, 32))
        border_pen.setWidthF(1.2)
        painter.setPen(border_pen)
        painter.drawPath(path)
