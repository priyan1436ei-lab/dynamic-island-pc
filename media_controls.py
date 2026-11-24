import ctypes
import os
import webbrowser

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_SNAPSHOT = 0x2C
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

class MediaControls:
    @staticmethod
    def _send_key(vk_code):
        try:
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        except Exception as e:
            print(f"Key event error: {e}")

    @staticmethod
    def play_pause():
        MediaControls._send_key(VK_MEDIA_PLAY_PAUSE)

    @staticmethod
    def next_track():
        MediaControls._send_key(VK_MEDIA_NEXT_TRACK)

    @staticmethod
    def prev_track():
        MediaControls._send_key(VK_MEDIA_PREV_TRACK)

    @staticmethod
    def volume_up():
        MediaControls._send_key(VK_VOLUME_UP)

    @staticmethod
    def volume_down():
        MediaControls._send_key(VK_VOLUME_DOWN)

    @staticmethod
    def volume_mute():
        MediaControls._send_key(VK_VOLUME_MUTE)

    @staticmethod
    def take_screenshot():
        MediaControls._send_key(VK_SNAPSHOT)

    @staticmethod
    def lock_workstation():
        try:
            ctypes.windll.user32.LockWorkStation()
        except Exception as e:
            print(f"Lock screen error: {e}")

    # App Launchers
    @staticmethod
    def launch_calc():
        try:
            os.startfile("calc.exe")
        except Exception as e:
            print(f"Launch calc error: {e}")

    @staticmethod
    def launch_notepad():
        try:
            os.startfile("notepad.exe")
        except Exception as e:
            print(f"Launch notepad error: {e}")

    @staticmethod
    def launch_explorer():
        try:
            os.startfile("explorer.exe")
        except Exception as e:
            print(f"Launch explorer error: {e}")

    @staticmethod
    def launch_taskmgr():
        try:
            os.startfile("taskmgr.exe")
        except Exception as e:
            print(f"Launch taskmgr error: {e}")

    @staticmethod
    def launch_browser():
        try:
            webbrowser.open("https://www.google.com")
        except Exception as e:
            print(f"Launch browser error: {e}")
