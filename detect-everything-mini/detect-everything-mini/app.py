from __future__ import annotations

import argparse
from pathlib import Path

from detector import EverythingDetector


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


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
        raise ValueError("Không tìm thấy ảnh hoặc video được hỗ trợ.")

    return sources


def build_output_path(
    source: Path,
    output_arg: str | None,
    multiple: bool,
    default_output_dir: Path,
) -> Path:
    extension = source.suffix.lower()
    output_extension = ".jpg" if extension in IMAGE_EXTENSIONS else ".mp4"
    default_name = f"{source.stem}_detected{output_extension}"

    if not output_arg:
        return default_output_dir / default_name

    output = Path(output_arg)
    if multiple or output.is_dir() or not output.suffix:
        return output / default_name

    return output


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
    parser = argparse.ArgumentParser(
        description="Detect Everything trên ảnh hoặc video bằng YOLO-World."
    )
    parser.add_argument(
        "--source",
        required=True,
        nargs="+",
        help="Một hoặc nhiều đường dẫn ảnh/video/thư mục đầu vào.",
    )
    parser.add_argument(
        "--classes",
        required=True,
        type=parse_classes,
        help='Các vật muốn tìm, cách nhau bằng dấu phẩy. Ví dụ: "person,laptop,phone"',
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

    detector = EverythingDetector(
        model_name=args.model,
        confidence=args.confidence,
        image_size=args.image_size,
    )
    detector.set_classes(args.classes)

    print("Đối tượng cần tìm:", ", ".join(args.classes))
    print(f"Số file cần xử lý: {len(sources)}")

    for index, source in enumerate(sources, start=1):
        extension = source.suffix.lower()
        output = build_output_path(source, args.output, multiple, default_output_dir)

        print(f"\n[{index}/{len(sources)}] Đang xử lý: {source}")
        if extension in IMAGE_EXTENSIONS:
            counts = detector.detect_image(str(source), str(output))
            print_counts("Kết quả trên ảnh:", counts)
        else:
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

        print(f"Đã lưu kết quả tại: {output.resolve()}")


if __name__ == "__main__":
    main()
