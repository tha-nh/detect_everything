from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from detector import EverythingDetector


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


class DetectEverythingApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Detect Everything Mini")
        self.root.geometry("980x700")
        self.root.minsize(840, 620)

        self.output_dir = Path(__file__).resolve().parent / "output"
        self.current_output_dir = self.output_dir
        self.last_outputs: list[Path] = []
        self.result_rows: dict[str, Path] = {}
        self.source_var = tk.StringVar()
        self.sources: list[Path] = []
        self.classes_var = tk.StringVar(
            value="person, laptop, mobile phone, bottle"
        )
        self.confidence_var = tk.DoubleVar(value=0.15)
        self.image_size_var = tk.IntVar(value=1280)
        self.status_var = tk.StringVar(value="Chọn một ảnh hoặc video để bắt đầu.")
        self.file_count_var = tk.StringVar(value="0")
        self.detected_count_var = tk.StringVar(value="0")

        self._build_ui()

    def _configure_styles(self) -> None:
        palette = {
            "bg": "#f4f7fb",
            "surface": "#ffffff",
            "surface_alt": "#f8fafc",
            "text": "#111827",
            "muted": "#657084",
            "border": "#dde5ef",
            "primary": "#0f766e",
            "primary_hover": "#115e59",
            "accent": "#f59e0b",
            "accent_soft": "#fff7ed",
            "success": "#15803d",
        }
        self.palette = palette

        self.root.configure(bg=palette["bg"])

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), foreground=palette["text"])
        style.configure("App.TFrame", background=palette["bg"])
        style.configure("Card.TFrame", background=palette["surface"], relief="solid", borderwidth=1)
        style.configure("Panel.TFrame", background=palette["surface"])
        style.configure("Soft.TFrame", background=palette["surface_alt"])
        style.configure("Accent.TFrame", background=palette["accent_soft"])
        style.configure("Header.TFrame", background=palette["bg"])
        style.configure("Brand.TLabel", background=palette["primary"], foreground="#ffffff", font=("Segoe UI", 13, "bold"))
        style.configure("Title.TLabel", background=palette["bg"], foreground=palette["text"], font=("Segoe UI", 21, "bold"))
        style.configure("Subtitle.TLabel", background=palette["bg"], foreground=palette["muted"], font=("Segoe UI", 10))
        style.configure("Kicker.TLabel", background=palette["bg"], foreground=palette["primary"], font=("Segoe UI", 9, "bold"))
        style.configure("Section.TLabel", background=palette["surface"], foreground=palette["text"], font=("Segoe UI", 11, "bold"))
        style.configure("Body.TLabel", background=palette["surface"], foreground=palette["muted"], font=("Segoe UI", 9))
        style.configure("SoftBody.TLabel", background=palette["surface_alt"], foreground=palette["muted"], font=("Segoe UI", 9))
        style.configure("StatValue.TLabel", background=palette["surface_alt"], foreground=palette["text"], font=("Segoe UI", 17, "bold"))
        style.configure("StatLabel.TLabel", background=palette["surface_alt"], foreground=palette["muted"], font=("Segoe UI", 8, "bold"))
        style.configure("Status.TLabel", background=palette["accent_soft"], foreground=palette["primary"], font=("Segoe UI", 9, "bold"))
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor=palette["border"], lightcolor=palette["border"], darkcolor=palette["border"], padding=8)
        style.configure("TSpinbox", fieldbackground="#ffffff", bordercolor=palette["border"], padding=5)
        style.configure("Primary.TButton", background=palette["primary"], foreground="#ffffff", borderwidth=0, focusthickness=0, padding=(16, 9), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", palette["primary_hover"]), ("disabled", "#9ca3af")], foreground=[("disabled", "#eef2f6")])
        style.configure("Accent.TButton", background=palette["accent_soft"], foreground="#9a3412", borderwidth=0, padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton", background=[("active", "#ffedd5"), ("disabled", "#edf1f7")], foreground=[("disabled", "#94a3b8")])
        style.configure("Ghost.TButton", background=palette["surface_alt"], foreground=palette["text"], borderwidth=0, padding=(12, 8))
        style.map("Ghost.TButton", background=[("active", "#edf2f7")])
        style.configure("Horizontal.TProgressbar", troughcolor="#dbe4ef", background=palette["primary"], bordercolor=palette["bg"], lightcolor=palette["primary"], darkcolor=palette["primary"])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground=palette["text"], rowheight=27, borderwidth=0)
        style.configure("Treeview.Heading", background=palette["surface_alt"], foreground=palette["muted"], font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#ccfbf1")], foreground=[("selected", palette["text"])])

    def _make_stat(self, parent: ttk.Frame, column: int, value_var: tk.StringVar, label: str) -> None:
        stat = ttk.Frame(parent, padding=(12, 10), style="Soft.TFrame")
        stat.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))
        ttk.Label(stat, textvariable=value_var, style="StatValue.TLabel").pack(anchor="w")
        ttk.Label(stat, text=label.upper(), style="StatLabel.TLabel").pack(anchor="w", pady=(2, 0))

    def _build_ui(self) -> None:
        self._configure_styles()

        container = ttk.Frame(self.root, padding=18, style="App.TFrame")
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0, minsize=300)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="Header.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="DE",
            anchor="center",
            style="Brand.TLabel",
            padding=(12, 9),
        ).grid(row=0, column=0, rowspan=3, sticky="nsw", padx=(0, 12))

        ttk.Label(
            header,
            text="YOLO-WORLD DETECTOR",
            style="Kicker.TLabel",
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(
            header,
            text="Detect Everything Mini",
            style="Title.TLabel",
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(
            header,
            text="Nhận diện ảnh và video bằng YOLO-World, lưu kết quả vào thư mục output.",
            style="Subtitle.TLabel",
            wraplength=720,
        ).grid(row=2, column=1, sticky="w", pady=(4, 0))

        input_card = ttk.Frame(container, padding=16, style="Card.TFrame")
        input_card.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        input_card.columnconfigure(0, weight=1)

        ttk.Label(input_card, text="Nguồn dữ liệu", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            input_card,
            text="Chọn một hoặc nhiều ảnh/video, hoặc quét cả thư mục.",
            style="Body.TLabel",
            wraplength=270,
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        source_entry = ttk.Entry(input_card, textvariable=self.source_var)
        source_entry.grid(row=2, column=0, sticky="ew")

        file_buttons = ttk.Frame(input_card, style="Panel.TFrame")
        file_buttons.grid(row=3, column=0, sticky="ew", pady=(10, 18))
        file_buttons.columnconfigure((0, 1, 2), weight=1, uniform="file_buttons")

        ttk.Button(file_buttons, text="Chọn file", command=self.choose_file, style="Ghost.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(file_buttons, text="Nhiều file", command=self.choose_files, style="Ghost.TButton").grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(file_buttons, text="Thư mục", command=self.choose_folder, style="Ghost.TButton").grid(row=0, column=2, sticky="ew", padx=(6, 0))

        ttk.Label(input_card, text="Đối tượng cần tìm", style="Section.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Label(
            input_card,
            text="Nhập class bằng tiếng Anh, cách nhau bằng dấu phẩy.",
            style="Body.TLabel",
            wraplength=270,
        ).grid(row=5, column=0, sticky="w", pady=(4, 10))

        ttk.Entry(input_card, textvariable=self.classes_var).grid(row=6, column=0, sticky="ew")
        ttk.Label(
            input_card,
            text="Ví dụ: person, laptop, mobile phone, red cup",
            style="Body.TLabel",
        ).grid(row=7, column=0, sticky="w", pady=(7, 18))

        ttk.Label(input_card, text="Cấu hình detect", style="Section.TLabel").grid(row=8, column=0, sticky="w")
        config_grid = ttk.Frame(input_card, style="Panel.TFrame")
        config_grid.grid(row=9, column=0, sticky="ew", pady=(10, 18))
        config_grid.columnconfigure((0, 1), weight=1, uniform="config")

        confidence_frame = ttk.Frame(config_grid, style="Panel.TFrame")
        confidence_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(confidence_frame, text="Confidence", style="Body.TLabel").pack(anchor="w")
        ttk.Spinbox(
            confidence_frame,
            from_=0.05,
            to=1.0,
            increment=0.05,
            textvariable=self.confidence_var,
            width=8,
        ).pack(fill="x", pady=(5, 0))

        image_size_frame = ttk.Frame(config_grid, style="Panel.TFrame")
        image_size_frame.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(image_size_frame, text="Image size", style="Body.TLabel").pack(anchor="w")
        ttk.Spinbox(
            image_size_frame,
            from_=640,
            to=1920,
            increment=160,
            textvariable=self.image_size_var,
            width=8,
        ).pack(fill="x", pady=(5, 0))

        self.run_button = ttk.Button(
            input_card,
            text="Chạy detect",
            command=self.start_detection,
            style="Primary.TButton",
        )
        self.run_button.grid(row=10, column=0, sticky="ew", ipady=2)

        ttk.Label(
            input_card,
            text="Mẹo: giảm confidence để hiện nhiều box hơn, tăng image size để bắt vật nhỏ tốt hơn.",
            style="Body.TLabel",
            wraplength=270,
        ).grid(row=11, column=0, sticky="w", pady=(12, 0))

        output_card = ttk.Frame(container, padding=16, style="Card.TFrame")
        output_card.grid(row=1, column=1, sticky="nsew")
        output_card.columnconfigure(0, weight=1)
        output_card.rowconfigure(5, weight=1)

        stats = ttk.Frame(output_card, style="Panel.TFrame")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        stats.columnconfigure((0, 1), weight=1, uniform="stats")
        self._make_stat(stats, 0, self.file_count_var, "File đã chọn")
        self._make_stat(stats, 1, self.detected_count_var, "Đối tượng")

        ttk.Label(output_card, text="Tiến trình", style="Section.TLabel").grid(row=1, column=0, sticky="w")
        status_bar = ttk.Frame(output_card, padding=(12, 10), style="Accent.TFrame")
        status_bar.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        status_bar.columnconfigure(0, weight=1)

        ttk.Label(
            status_bar,
            textvariable=self.status_var,
            style="Status.TLabel",
            wraplength=520,
        ).grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(
            output_card,
            orient="horizontal",
            mode="determinate",
        )
        self.progress.grid(row=3, column=0, sticky="ew", pady=(0, 18))

        actions = ttk.Frame(output_card, style="Panel.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        actions.columnconfigure((0, 1), weight=1, uniform="actions")

        self.open_result_button = ttk.Button(
            actions,
            text="Mở kết quả",
            command=self.open_result,
            state="disabled",
            style="Accent.TButton",
        )
        self.open_result_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.open_output_button = ttk.Button(
            actions,
            text="Mở output",
            command=self.open_output_folder,
            style="Ghost.TButton",
        )
        self.open_output_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        table_frame = ttk.Frame(output_card, style="Panel.TFrame")
        table_frame.grid(row=5, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(1, weight=1)

        ttk.Label(table_frame, text="Kết quả", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.results_table = ttk.Treeview(
            table_frame,
            columns=("file", "counts", "output"),
            show="headings",
            height=6,
        )
        self.results_table.heading("file", text="File")
        self.results_table.heading("counts", text="Detect")
        self.results_table.heading("output", text="Output")
        self.results_table.column("file", width=120, minwidth=90, anchor="w", stretch=True)
        self.results_table.column("counts", width=140, minwidth=110, anchor="w", stretch=True)
        self.results_table.column("output", width=160, minwidth=120, anchor="w", stretch=True)
        self.results_table.grid(row=1, column=0, sticky="nsew")
        self.results_table.bind("<Double-1>", lambda _event: self.open_result())

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.results_table.yview,
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.results_table.configure(yscrollcommand=scrollbar.set)

    def choose_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Chọn ảnh hoặc video",
            filetypes=[
                ("Ảnh và video", "*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.avi *.mov *.mkv *.wmv"),
                ("Tất cả file", "*.*"),
            ],
        )
        if filename:
            self.sources = [Path(filename)]
            self.current_output_dir = self.output_dir
            self.source_var.set(filename)
            self.file_count_var.set("1")
            self.detected_count_var.set("0")
            self.status_var.set(f"Sẵn sàng xử lý: {Path(filename).name}")

    def choose_files(self) -> None:
        filenames = filedialog.askopenfilenames(
            title="Chọn ảnh hoặc video",
            filetypes=[
                ("Ảnh và video", "*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.avi *.mov *.mkv *.wmv"),
                ("Tất cả file", "*.*"),
            ],
        )
        if filenames:
            self.sources = [Path(filename) for filename in filenames]
            self.current_output_dir = self.output_dir
            self.source_var.set(f"Đã chọn {len(self.sources)} file")
            self.file_count_var.set(str(len(self.sources)))
            self.detected_count_var.set("0")
            self.status_var.set(f"Sẵn sàng xử lý {len(self.sources)} file.")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh hoặc video")
        if folder:
            folder_path = Path(folder)
            self.sources = self._collect_sources([folder_path])
            self.current_output_dir = self.output_dir / folder_path.name
            self.source_var.set(f"{folder} ({len(self.sources)} file được hỗ trợ)")
            self.file_count_var.set(str(len(self.sources)))
            self.detected_count_var.set("0")
            self.status_var.set(f"Tìm thấy {len(self.sources)} file được hỗ trợ trong thư mục.")

    def start_detection(self) -> None:
        typed_source = Path(self.source_var.get().strip())
        sources = self.sources or self._collect_sources([typed_source])
        classes = [
            item.strip()
            for item in self.classes_var.get().split(",")
            if item.strip()
        ]
        if self.sources:
            output_dir = self.current_output_dir
        elif typed_source.is_dir():
            output_dir = self.output_dir / typed_source.name
        else:
            output_dir = self.output_dir

        if not sources:
            messagebox.showerror("Thiếu file", "Hãy chọn ảnh hoặc video hợp lệ.")
            return
        if not classes:
            messagebox.showerror(
                "Thiếu đối tượng",
                "Hãy nhập ít nhất một đối tượng cần tìm.",
            )
            return

        unsupported = [
            source
            for source in sources
            if source.suffix.lower() not in SUPPORTED_EXTENSIONS
        ]
        if unsupported:
            messagebox.showerror(
                "Không hỗ trợ",
                f"Có {len(unsupported)} file chưa được hỗ trợ.",
            )
            return

        self.run_button.configure(state="disabled")
        self.open_result_button.configure(state="disabled")
        self.last_outputs = []
        self.result_rows = {}
        self.current_output_dir = output_dir
        self.file_count_var.set(str(len(sources)))
        self.detected_count_var.set("0")
        for row_id in self.results_table.get_children():
            self.results_table.delete(row_id)
        self.progress["value"] = 0
        self.status_var.set(
            "Đang tải model và xử lý. Lần chạy đầu cần Internet để tải model..."
        )

        threading.Thread(
            target=self._run_detection,
            args=(sources, classes, output_dir),
            daemon=True,
        ).start()

    def _run_detection(
        self,
        sources: list[Path],
        classes: list[str],
        output_dir: Path,
    ) -> None:
        try:
            detector = EverythingDetector(
                model_name="yolov8s-worldv2.pt",
                confidence=float(self.confidence_var.get()),
                image_size=int(self.image_size_var.get()),
            )
            detector.set_classes(classes)

            output_dir.mkdir(parents=True, exist_ok=True)

            summaries: list[str] = []
            result_items: list[tuple[str, str, Path]] = []
            outputs: list[Path] = []
            total_sources = len(sources)

            for index, source in enumerate(sources):
                self._set_status(f"Đang xử lý {index + 1}/{total_sources}: {source.name}")

                if source.suffix.lower() in IMAGE_EXTENSIONS:
                    output = self._next_output_path(output_dir / f"{source.stem}_detected.jpg")
                    counts = detector.detect_image(str(source), str(output))
                    self._set_progress((index + 1) * 100 / total_sources)
                else:
                    output = self._next_output_path(output_dir / f"{source.stem}_detected.mp4")
                    counts = detector.detect_video(
                        str(source),
                        str(output),
                        progress_callback=lambda current, total, file_index=index: (
                            self._update_progress(file_index, total_sources, current, total)
                        ),
                    )

                count_text = (
                    ", ".join(f"{name}: {count}" for name, count in counts.items())
                    if counts
                    else "Không tìm thấy đối tượng phù hợp"
                )
                summaries.append(f"{source.name}: {count_text}\nFile: {output}")
                result_items.append((source.name, count_text, output))
                outputs.append(output)

            self.root.after(
                0,
                lambda: self._finish_success("\n\n".join(summaries), result_items, outputs),
            )
        except Exception as exc:
            self.root.after(0, lambda: self._finish_error(str(exc)))

    def _update_progress(
        self,
        file_index: int,
        total_sources: int,
        current: int,
        total: int,
    ) -> None:
        if total > 0:
            file_progress = current / total
            value = (file_index + file_progress) * 100 / total_sources
            self._set_progress(value)
            self._set_status(f"Đang xử lý video {file_index + 1}/{total_sources}, frame {current}/{total}...")
        else:
            self._set_status(f"Đã xử lý {current} frame...")

    def _finish_success(
        self,
        summary: str,
        result_items: list[tuple[str, str, Path]],
        outputs: list[Path],
    ) -> None:
        self.progress["value"] = 100
        self.last_outputs = outputs
        self.result_rows = {}
        detected_total = 0
        for file_name, count_text, output in result_items:
            detected_total += sum(
                int(part.rsplit(": ", 1)[1])
                for part in count_text.split(", ")
                if ": " in part and part.rsplit(": ", 1)[1].isdigit()
            )
            row_id = self.results_table.insert(
                "",
                "end",
                values=(file_name, count_text, str(output)),
            )
            self.result_rows[row_id] = output
        self.run_button.configure(state="normal")
        self.open_result_button.configure(state="normal")
        self.detected_count_var.set(str(detected_total))
        self.status_var.set("Hoàn thành. Kết quả đã lưu trong thư mục output.")
        messagebox.showinfo(
            "Hoàn thành",
            f"Kết quả:\n{summary}",
        )

    def _finish_error(self, error: str) -> None:
        self.run_button.configure(state="normal")
        self.status_var.set("Xử lý thất bại.")
        messagebox.showerror("Có lỗi xảy ra", error)

    def open_result(self) -> None:
        if not self.last_outputs:
            messagebox.showinfo("Chưa có kết quả", "Hãy chạy detect trước.")
            return

        selected = self.results_table.selection()
        if selected:
            target = self.result_rows.get(selected[0], self.current_output_dir)
        else:
            target = self.last_outputs[0] if len(self.last_outputs) == 1 else self.current_output_dir
        self._open_path(target)

    def open_output_folder(self) -> None:
        self.current_output_dir.mkdir(parents=True, exist_ok=True)
        self._open_path(self.current_output_dir)

    @staticmethod
    def _open_path(path: Path) -> None:
        if not path.exists():
            messagebox.showerror("Không tìm thấy", f"Không tìm thấy: {path}")
            return
        os.startfile(path)

    def _set_progress(self, value: float) -> None:
        self.root.after(0, lambda: self.progress.configure(value=value))

    def _set_status(self, message: str) -> None:
        self.root.after(0, lambda: self.status_var.set(message))

    @staticmethod
    def _collect_sources(paths: list[Path]) -> list[Path]:
        sources: list[Path] = []
        for path in paths:
            if path.is_dir():
                sources.extend(
                    item
                    for item in sorted(path.iterdir())
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS
                )
            elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                sources.append(path)
        return sources

    @staticmethod
    def _next_output_path(path: Path) -> Path:
        if not path.exists():
            return path

        for index in range(2, 1000):
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate

        raise RuntimeError(f"Không thể tạo tên file đầu ra cho: {path}")


def main() -> None:
    root = tk.Tk()
    DetectEverythingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
