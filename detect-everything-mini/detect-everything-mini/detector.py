from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Callable

import cv2
from ultralytics import YOLO


Box = tuple[float, float, float, float]
TrackedDetection = tuple[str, int, Box]


class EverythingDetector:
    """Detect objects from text prompts using YOLO-World."""

    def __init__(
        self,
        model_name: str = "yolov8s-worldv2.pt",
        confidence: float = 0.15,
        image_size: int = 1280,
    ) -> None:
        if not 0 < confidence <= 1:
            raise ValueError("confidence phải nằm trong khoảng (0, 1].")
        if image_size < 320:
            raise ValueError("image_size phải từ 320 trở lên.")

        print(f"Đang tải model: {model_name}")
        self.model = YOLO(model_name)
        self.confidence = confidence
        self.image_size = image_size
        self.class_names: list[str] = []

    def set_classes(self, class_names: list[str]) -> None:
        cleaned = [name.strip() for name in class_names if name.strip()]
        if not cleaned:
            raise ValueError("Danh sách đối tượng cần tìm không được để trống.")

        self.class_names = cleaned
        self.model.set_classes(cleaned)

    def detect_image(self, input_path: str, output_path: str) -> dict[str, int]:
        source = Path(input_path)
        if not source.is_file():
            raise FileNotFoundError(f"Không tìm thấy ảnh: {source}")

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        results = self.model.predict(
            source=str(source),
            conf=self.confidence,
            imgsz=self.image_size,
            verbose=False,
        )

        result = results[0]
        annotated = result.plot()

        if not cv2.imwrite(str(destination), annotated):
            raise RuntimeError(f"Không thể lưu ảnh kết quả: {destination}")

        return self._count_objects(result)

    def detect_video(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, int]:
        source = Path(input_path)
        if not source.is_file():
            raise FileNotFoundError(f"Không tìm thấy video: {source}")

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise RuntimeError(f"Không mở được video: {source}")

        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        # mp4v tương thích tốt trên Windows và tạo file MP4.
        writer = cv2.VideoWriter(
            str(destination),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        if not writer.isOpened():
            capture.release()
            raise RuntimeError(f"Không tạo được video đầu ra: {destination}")

        tracked_objects: set[tuple[str, int]] = set()
        canonical_by_raw_track: dict[tuple[str, int], int] = {}
        track_states: dict[tuple[str, int], tuple[Box, int]] = {}
        next_canonical_id = 1
        fallback_counts: Counter[str] = Counter()
        used_tracking = False
        processed_frames = 0

        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break

                results = self.model.track(
                    source=frame,
                    conf=self.confidence,
                    imgsz=self.image_size,
                    persist=True,
                    tracker="bytetrack.yaml",
                    verbose=False,
                )
                result = results[0]
                writer.write(result.plot())

                detections = self._tracked_detections(result)
                if detections:
                    used_tracking = True
                    current_frame_objects: set[tuple[str, int]] = set()

                    for class_name, raw_track_id, box in detections:
                        raw_key = (class_name, raw_track_id)
                        if raw_key in canonical_by_raw_track:
                            canonical_id = canonical_by_raw_track[raw_key]
                        else:
                            canonical_id = self._match_recent_track(
                                class_name=class_name,
                                box=box,
                                frame_index=processed_frames,
                                track_states=track_states,
                                used_in_frame=current_frame_objects,
                            )
                            if canonical_id is None:
                                canonical_id = next_canonical_id
                                next_canonical_id += 1
                            canonical_by_raw_track[raw_key] = canonical_id

                        canonical_key = (class_name, canonical_id)
                        current_frame_objects.add(canonical_key)
                        track_states[canonical_key] = (box, processed_frames)

                    tracked_objects.update(current_frame_objects)
                elif not used_tracking:
                    fallback_counts.update(self._count_objects(result))
                processed_frames += 1

                if progress_callback:
                    progress_callback(processed_frames, total_frames)
        finally:
            capture.release()
            writer.release()

        if used_tracking:
            counts: Counter[str] = Counter()
            for class_name, _track_id in tracked_objects:
                counts[class_name] += 1
            return dict(counts)

        return dict(fallback_counts)

    @staticmethod
    def _count_objects(result) -> dict[str, int]:
        counts: Counter[str] = Counter()

        if result.boxes is None or result.boxes.cls is None:
            return {}

        class_ids = result.boxes.cls.cpu().tolist()
        names = result.names

        for class_id in class_ids:
            counts[names[int(class_id)]] += 1

        return dict(counts)

    @staticmethod
    def _tracked_detections(result) -> list[TrackedDetection]:
        if (
            result.boxes is None
            or result.boxes.cls is None
            or result.boxes.id is None
            or result.boxes.xyxy is None
        ):
            return []

        class_ids = result.boxes.cls.cpu().tolist()
        track_ids = result.boxes.id.cpu().tolist()
        boxes = result.boxes.xyxy.cpu().tolist()
        names = result.names

        return [
            (
                names[int(class_id)],
                int(track_id),
                tuple(float(value) for value in box),
            )
            for class_id, track_id, box in zip(class_ids, track_ids, boxes)
        ]

    @classmethod
    def _match_recent_track(
        cls,
        class_name: str,
        box: Box,
        frame_index: int,
        track_states: dict[tuple[str, int], tuple[Box, int]],
        used_in_frame: set[tuple[str, int]],
    ) -> int | None:
        best_id: int | None = None
        best_score = 0.0

        for (state_class, canonical_id), (old_box, last_frame) in track_states.items():
            canonical_key = (state_class, canonical_id)
            gap = frame_index - last_frame
            if (
                state_class != class_name
                or canonical_key in used_in_frame
                or gap <= 0
                or gap > 45
            ):
                continue

            iou = cls._box_iou(box, old_box)
            center_distance = cls._normalized_center_distance(box, old_box)
            area_ratio = cls._area_ratio(box, old_box)

            same_place = iou >= 0.25
            nearby_after_short_gap = (
                gap <= 15
                and center_distance <= 0.08
                and 0.35 <= area_ratio <= 2.8
            )

            if not same_place and not nearby_after_short_gap:
                continue

            score = iou + max(0.0, 0.08 - center_distance)
            if score > best_score:
                best_score = score
                best_id = canonical_id

        return best_id

    @staticmethod
    def _box_iou(first: Box, second: Box) -> float:
        x1 = max(first[0], second[0])
        y1 = max(first[1], second[1])
        x2 = min(first[2], second[2])
        y2 = min(first[3], second[3])
        intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        if intersection == 0:
            return 0.0

        first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
        second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
        union = first_area + second_area - intersection
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _normalized_center_distance(first: Box, second: Box) -> float:
        first_width = max(1.0, first[2] - first[0])
        first_height = max(1.0, first[3] - first[1])
        second_width = max(1.0, second[2] - second[0])
        second_height = max(1.0, second[3] - second[1])
        average_size = (first_width + first_height + second_width + second_height) / 4

        first_center = ((first[0] + first[2]) / 2, (first[1] + first[3]) / 2)
        second_center = ((second[0] + second[2]) / 2, (second[1] + second[3]) / 2)
        distance = (
            (first_center[0] - second_center[0]) ** 2
            + (first_center[1] - second_center[1]) ** 2
        ) ** 0.5
        return distance / average_size

    @staticmethod
    def _area_ratio(first: Box, second: Box) -> float:
        first_area = max(1.0, first[2] - first[0]) * max(1.0, first[3] - first[1])
        second_area = max(1.0, second[2] - second[0]) * max(1.0, second[3] - second[1])
        return first_area / second_area
