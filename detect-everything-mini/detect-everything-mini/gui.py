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
        self.root.geometry("860x560")
        self.root.minsize(760, 500)

        self.output_dir = Path(__file__).resolve().parent / "output"
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

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Detect Everything Mini",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=(
                "Chọn ảnh/video, nhập các vật muốn tìm bằng tiếng Anh, "
                "sau đó nhấn Chạy detect."
            ),
        ).pack(anchor="w", pady=(4, 18))

        file_frame = ttk.LabelFrame(container, text="1. File đầu vào", padding=12)
        file_frame.pack(fill="x")

        ttk.Entry(file_frame, textvariable=self.source_var).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            file_frame,
            text="Chọn file",
            command=self.choose_file,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            file_frame,
            text="Chọn nhiều file",
            command=self.choose_files,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            file_frame,
            text="Chọn thư mục",
            command=self.choose_folder,
        ).pack(side="left", padx=(8, 0))

        class_frame = ttk.LabelFrame(
            container,
            text="2. Đối tượng cần tìm",
            padding=12,
        )
        class_frame.pack(fill="x", pady=12)

        ttk.Entry(class_frame, textvariable=self.classes_var).pack(fill="x")
        ttk.Label(
            class_frame,
            text='Ví dụ: person, laptop, mobile phone, red cup',
        ).pack(anchor="w", pady=(6, 0))

        config_frame = ttk.LabelFrame(container, text="3. Cấu hình", padding=12)
        config_frame.pack(fill="x")

        ttk.Label(config_frame, text="Confidence:").pack(side="left")
        ttk.Spinbox(
            config_frame,
            from_=0.05,
            to=1.0,
            increment=0.05,
            textvariable=self.confidence_var,
            width=8,
        ).pack(side="left", padx=(8, 18))

        ttk.Label(config_frame, text="Image size:").pack(side="left")
        ttk.Spinbox(
            config_frame,
            from_=640,
            to=1920,
            increment=160,
            textvariable=self.image_size_var,
            width=8,
        ).pack(side="left", padx=(8, 18))

        self.run_button = ttk.Button(
            config_frame,
            text="Chạy detect",
            command=self.start_detection,
        )
        self.run_button.pack(side="left")

        self.progress = ttk.Progressbar(
            container,
            orient="horizontal",
            mode="determinate",
        )
        self.progress.pack(fill="x", pady=(18, 8))

        result_frame = ttk.Frame(container)
        result_frame.pack(fill="x", pady=(0, 8))

        self.open_result_button = ttk.Button(
            result_frame,
            text="Mở kết quả",
            command=self.open_result,
            state="disabled",
        )
        self.open_result_button.pack(side="left")

        self.open_output_button = ttk.Button(
            result_frame,
            text="Mở thư mục output",
            command=self.open_output_folder,
        )
        self.open_output_button.pack(side="left", padx=(8, 0))

        table_frame = ttk.LabelFrame(container, text="Kết quả", padding=8)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))

        self.results_table = ttk.Treeview(
            table_frame,
            columns=("file", "counts", "output"),
            show="headings",
            height=7,
        )
        self.results_table.heading("file", text="File")
        self.results_table.heading("counts", text="Detect")
        self.results_table.heading("output", text="Output")
        self.results_table.column("file", width=180, anchor="w")
        self.results_table.column("counts", width=260, anchor="w")
        self.results_table.column("output", width=360, anchor="w")
        self.results_table.pack(side="left", fill="both", expand=True)
        self.results_table.bind("<Double-1>", lambda _event: self.open_result())

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.results_table.yview,
        )
        scrollbar.pack(side="right", fill="y")
        self.results_table.configure(yscrollcommand=scrollbar.set)

        ttk.Label(
            container,
            textvariable=self.status_var,
            wraplength=660,
        ).pack(anchor="w")

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
            self.source_var.set(filename)

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
            self.source_var.set(f"Đã chọn {len(self.sources)} file")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh hoặc video")
        if folder:
            self.sources = self._collect_sources([Path(folder)])
            self.source_var.set(f"{folder} ({len(self.sources)} file được hỗ trợ)")

    def start_detection(self) -> None:
        sources = self.sources or self._collect_sources([Path(self.source_var.get().strip())])
        classes = [
            item.strip()
            for item in self.classes_var.get().split(",")
            if item.strip()
        ]

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
        for row_id in self.results_table.get_children():
            self.results_table.delete(row_id)
        self.progress["value"] = 0
        self.status_var.set(
            "Đang tải model và xử lý. Lần chạy đầu cần Internet để tải model..."
        )

        threading.Thread(
            target=self._run_detection,
            args=(sources, classes),
            daemon=True,
        ).start()

    def _run_detection(self, sources: list[Path], classes: list[str]) -> None:
        try:
            detector = EverythingDetector(
                model_name="yolov8s-worldv2.pt",
                confidence=float(self.confidence_var.get()),
                image_size=int(self.image_size_var.get()),
            )
            detector.set_classes(classes)

            output_dir = self.output_dir
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
        for file_name, count_text, output in result_items:
            row_id = self.results_table.insert(
                "",
                "end",
                values=(file_name, count_text, str(output)),
            )
            self.result_rows[row_id] = output
        self.run_button.configure(state="normal")
        self.open_result_button.configure(state="normal")
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
            target = self.result_rows.get(selected[0], self.output_dir)
        else:
            target = self.last_outputs[0] if len(self.last_outputs) == 1 else self.output_dir
        self._open_path(target)

    def open_output_folder(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._open_path(self.output_dir)

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
