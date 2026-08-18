from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audio_detector import analyze_video_audio
from text_detector import TEXT_EXTENSIONS, TextFileDetector


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
SUPPORTED_EXTENSIONS = MEDIA_EXTENSIONS | TEXT_EXTENSIONS


def parse_classes(value: str) -> list[str]:
    classes = [item.strip() for item in value.split(",") if item.strip()]
    if not classes:
        raise argparse.ArgumentTypeError(
            "Hãy nhập ít nhất một đối tượng, ví dụ: person,laptop,phone"
        )
    return classes


def print_counts(title: str, counts: dict[str, int]) -> None:
    print(f"\n{title}")
    if not counts:
        print("- Không tìm thấy đối tượng phù hợp.")
        return

    for name, count in sorted(counts.items()):
        print(f"- {name}: {count}")


def collect_sources(paths: list[Path]) -> list[Path]:
    sources: list[Path] = []

    for path in paths:
        if path.is_dir():
            sources.extend(
                item
                for item in sorted(path.iterdir())
                if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS
            )
        elif path.is_file():
            sources.append(path)
        else:
            raise FileNotFoundError(f"Không tìm thấy file hoặc thư mục: {path}")

    unsupported = [
        source
        for source in sources
        if source.suffix.lower() not in SUPPORTED_EXTENSIONS
    ]
    if unsupported:
        names = ", ".join(str(source) for source in unsupported)
        raise ValueError(f"Có file chưa được hỗ trợ: {names}")

    if not sources:
        raise ValueError("Không tìm thấy ảnh, video hoặc file text được hỗ trợ.")

    return sources


def build_output_path(
    source: Path,
    output_arg: str | None,
    multiple: bool,
    default_output_dir: Path,
) -> Path:
    extension = source.suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        output_extension = ".jpg"
        default_name = f"{source.stem}_detected{output_extension}"
    elif extension in VIDEO_EXTENSIONS:
        output_extension = ".mp4"
        default_name = f"{source.stem}_detected{output_extension}"
    else:
        default_name = f"{source.stem}_{extension.lstrip('.')}_detected.html"

    if not output_arg:
        return default_output_dir / default_name

    output = Path(output_arg)
    if multiple or output.is_dir() or not output.suffix:
        return output / default_name

    return output


def next_output_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Không thể tạo tên file đầu ra cho: {path}")


def show_progress(current: int, total: int) -> None:
    if total > 0:
        percent = current * 100 / total
        print(
            f"\rĐang xử lý: {current}/{total} frame ({percent:5.1f}%)",
            end="",
            flush=True,
        )
    else:
        print(f"\rĐã xử lý {current} frame", end="", flush=True)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Detect Everything trên ảnh/video bằng YOLO-World và gán nhãn đoạn text trong tài liệu."
    )
    parser.add_argument(
        "--source",
        required=True,
        nargs="+",
        help="Một hoặc nhiều đường dẫn ảnh/video/text/thư mục đầu vào.",
    )
    parser.add_argument(
        "--classes",
        required=True,
        type=parse_classes,
        help='Vật hoặc nhãn text, cách nhau bằng dấu phẩy. Ví dụ: "person,laptop,invoice=hóa đơn tổng tiền"',
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.15,
        help="Ngưỡng tin cậy từ 0 đến 1. Mặc định: 0.15",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=1280,
        help="Kích thước ảnh đưa vào model. Tăng lên để bắt vật nhỏ tốt hơn. Mặc định: 1280",
    )
    parser.add_argument(
        "--model",
        default="yolov8s-worldv2.pt",
        help="Tên hoặc đường dẫn model. Mặc định: yolov8s-worldv2.pt",
    )
    parser.add_argument(
        "--output",
        help="Đường dẫn kết quả. Nếu bỏ trống, chương trình tự tạo trong output/.",
    )
    args = parser.parse_args()

    source_paths = [Path(value) for value in args.source]
    default_output_dir = Path("output")
    if len(source_paths) == 1 and source_paths[0].is_dir() and not args.output:
        default_output_dir = default_output_dir / source_paths[0].name

    try:
        sources = collect_sources(source_paths)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    multiple = len(sources) > 1

    detector = None
    text_detector = TextFileDetector(args.classes)

    print("Đối tượng cần tìm:", ", ".join(args.classes))
    print(f"Số file cần xử lý: {len(sources)}")

    for index, source in enumerate(sources, start=1):
        extension = source.suffix.lower()
        output = next_output_path(
            build_output_path(source, args.output, multiple, default_output_dir)
        )

        print(f"\n[{index}/{len(sources)}] Đang xử lý: {source}")
        if extension in IMAGE_EXTENSIONS:
            if detector is None:
                from detector import EverythingDetector

                detector = EverythingDetector(
                    model_name=args.model,
                    confidence=args.confidence,
                    image_size=args.image_size,
                )
                detector.set_classes(args.classes)
            counts = detector.detect_image(str(source), str(output))
            print_counts("Kết quả trên ảnh:", counts)
        elif extension in VIDEO_EXTENSIONS:
            if detector is None:
                from detector import EverythingDetector

                detector = EverythingDetector(
                    model_name=args.model,
                    confidence=args.confidence,
                    image_size=args.image_size,
                )
                detector.set_classes(args.classes)
            counts = detector.detect_video(
                str(source),
                str(output),
                progress_callback=show_progress,
            )
            print()
            print_counts(
                "Số vật thể ước tính trong video bằng tracking:",
                counts,
            )
            audio_report = analyze_video_audio(source, output, counts, args.classes)
            print(f"Đã lưu báo cáo video tại: {Path(audio_report.report_html).resolve()}")
            for status_item in audio_report.status:
                print(f"- {status_item}")
        else:
            counts = text_detector.detect_file(str(source), str(output))
            print_counts("Số đoạn theo từng nhãn:", counts)

        print(f"Đã lưu kết quả tại: {output.resolve()}")


if __name__ == "__main__":
    main()
