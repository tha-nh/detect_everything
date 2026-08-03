# Tech Stack
- Python app, UTF-8 source files.
- GUI uses built-in Tkinter/ttk; no custom GUI package in `requirements.txt`.
- Detection uses `ultralytics>=8.3.0` and `opencv-python>=4.10.0`.
- Bundled/default YOLO-World model filename is `yolov8s-worldv2.pt`; `weights/` and root model file may exist locally.
- Windows batch entrypoints: `setup_windows.bat`, `run_gui.bat`, `run_image_example.bat`.