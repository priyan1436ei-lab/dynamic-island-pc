---
## 7. How to Run & Build from Source
### Quick Launch (Ready Executable)
Simply double-click the standalone executable:
👉 **[DynamicIsland.exe](file:///G:/My%20Drive/New%20folder%20(6)/DynamicIsland.exe)** *(~27 MB, Self-contained, No Python installation required)*
### Run from Source
```bash
# 1. Install dependencies
python -m pip install psutil pillow
# 2. Launch the application
python main.py
```
### Compile into Standalone `.exe`
```bash
python -m PyInstaller --clean --onefile --noconsole --icon="app_icon.ico" --name="DynamicIsland" main.py
```
The output binary will be generated under the `dist/` directory.
---
## 8. Shortcuts & Interaction Cheat Sheet
| Interaction | Action |
| :--- | :--- |
| **Hover over Compact Island** | Expands island into full 6-tab card view (if enabled). |
| **Left Click on Compact Island** | Expands island immediately. |
| **Move Cursor away** | Automatically collapses back to sleek pill after 1.2 seconds. |
| **Click [▲ சுருக்கு] Button** | Instantly collapses expanded island. |
| **Right Click on Island** | Opens Context Menu: Toggle Expand, Settings, Exit. |
| **Click [📸 ஸ்கிரீன்ஷாட்]** | Captures screen and displays animated notification banner. |
| **Click [📋 மீண்டும் நகலெடு]** | Copies historic clipboard text back to Windows clipboard. |
| **Change Any Slider** | Live real-time visual resize of width, height, or margin. |
---
<p align="center">
  <b>Designed with ❤️ for Windows 10 & 11</b><br>
  <i>Experience the elegance of Apple's Dynamic Island with the power of Windows.</i>
</p>
