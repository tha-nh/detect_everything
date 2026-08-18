from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path

from text_detector import TextFileDetector


@dataclass(frozen=True)
class SpeechSegment:
    start: float
    end: float
    text: str
    label: str
    score: float
    summary: str


@dataclass(frozen=True)
class AudioVideoReport:
    source_video: str
    detected_video: str
    report_html: str
    report_json: str
    audio_preserved: bool
    status: list[str]
    visual_counts: dict[str, int]
    speech_label_counts: dict[str, int]
    speech_segments: list[SpeechSegment]


def analyze_video_audio(
    input_video: Path,
    detected_video: Path,
    visual_counts: dict[str, int],
    labels: list[str],
) -> AudioVideoReport:
    report_html = detected_video.with_name(f"{detected_video.stem}_report.html")
    report_json = detected_video.with_name(f"{detected_video.stem}_report.json")
    status: list[str] = []

    audio_preserved = mux_original_audio(input_video, detected_video, status)
    speech_segments = transcribe_and_label_speech(input_video, labels, status)
    speech_label_counts = Counter(segment.label for segment in speech_segments)

    report = AudioVideoReport(
        source_video=str(input_video),
        detected_video=str(detected_video),
        report_html=str(report_html),
        report_json=str(report_json),
        audio_preserved=audio_preserved,
        status=status,
        visual_counts=visual_counts,
        speech_label_counts=dict(speech_label_counts),
        speech_segments=speech_segments,
    )

    report_html.write_text(build_html_report(report), encoding="utf-8")
    report_json.write_text(
        json.dumps(_report_to_json(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def mux_original_audio(
    input_video: Path,
    detected_video: Path,
    status: list[str],
) -> bool:
    if shutil.which("ffmpeg") is None:
        status.append("Chưa tìm thấy ffmpeg nên video kết quả chưa được ghép lại audio gốc.")
        return False

    if not _video_has_audio(input_video):
        status.append("Video đầu vào không có audio track để ghép lại.")
        return False

    temporary_output = detected_video.with_name(f"{detected_video.stem}_with_audio_tmp.mp4")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(detected_video),
        "-i",
        str(input_video),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(temporary_output),
    ]
    result = _run_command(command)
    if result.returncode != 0 or not temporary_output.exists():
        status.append("Không ghép được audio gốc vào video kết quả.")
        temporary_output.unlink(missing_ok=True)
        return False

    temporary_output.replace(detected_video)
    status.append("Đã ghép audio gốc vào video kết quả.")
    return True


def transcribe_and_label_speech(
    input_video: Path,
    labels: list[str],
    status: list[str],
) -> list[SpeechSegment]:
    if shutil.which("ffmpeg") is None:
        status.append("Chưa tìm thấy ffmpeg nên chưa thể trích âm thanh để nhận dạng lời nói.")
        return []

    if not _video_has_audio(input_video):
        return []

    with tempfile.TemporaryDirectory(prefix="detect_everything_audio_") as temp_dir:
        audio_path = Path(temp_dir) / "audio.wav"
        extract_result = _run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_video),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "wav",
                str(audio_path),
            ]
        )
        if extract_result.returncode != 0 or not audio_path.exists():
            status.append("Không trích xuất được audio để nhận dạng lời nói.")
            return []

        raw_segments = _transcribe_with_available_model(audio_path, status)
        if not raw_segments:
            return []

    text_detector = TextFileDetector(labels)
    labeled_segments: list[SpeechSegment] = []
    for start, end, text in raw_segments:
        label, score = _classify_speech_text(text_detector, text)
        labeled_segments.append(
            SpeechSegment(
                start=start,
                end=end,
                text=text,
                label=label,
                score=score,
                summary=_summarize_text(text),
            )
        )

    status.append(f"Đã nhận dạng {len(labeled_segments)} đoạn lời nói.")
    return labeled_segments


def build_html_report(report: AudioVideoReport) -> str:
    visual_rows = _count_rows(report.visual_counts)
    speech_rows = _count_rows(report.speech_label_counts)
    status_items = "\n".join(f"<li>{escape(item)}</li>" for item in report.status)
    segment_rows = "\n".join(
        (
            "<tr>"
            f"<td>{_format_time(segment.start)} - {_format_time(segment.end)}</td>"
            f"<td>{escape(segment.text)}</td>"
            f"<td>{escape(segment.label)}</td>"
            f"<td>{segment.score:.2f}</td>"
            f"<td>{escape(segment.summary)}</td>"
            "</tr>"
        )
        for segment in report.speech_segments
    )
    if not segment_rows:
        segment_rows = (
            '<tr><td colspan="5">Chưa có transcript. Kiểm tra ffmpeg và faster-whisper/whisper '
            "nếu video có lời nói.</td></tr>"
        )

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Video Audio Report - {escape(Path(report.source_video).name)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fb;
      --surface: #ffffff;
      --text: #172033;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #0f766e;
      --accent-soft: #d8f3ee;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", Arial, sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 28px 0 12px; font-size: 18px; }}
    .muted {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-top: 20px;
    }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{
      background: #eef2f7;
      border-radius: 5px;
      padding: 2px 5px;
    }}
  </style>
</head>
<body>
<main>
  <h1>Báo cáo video</h1>
  <p class="muted">Nguồn: <code>{escape(report.source_video)}</code></p>
  <p class="muted">Video kết quả: <code>{escape(report.detected_video)}</code></p>

  <section class="grid">
    <div class="panel">
      <h2>Hình ảnh</h2>
      <table><tbody>{visual_rows}</tbody></table>
    </div>
    <div class="panel">
      <h2>Lời nói</h2>
      <table><tbody>{speech_rows}</tbody></table>
    </div>
    <div class="panel">
      <h2>Trạng thái</h2>
      <ul>{status_items}</ul>
    </div>
  </section>

  <section>
    <h2>Timeline lời nói</h2>
    <table>
      <thead>
        <tr>
          <th>Thời gian</th>
          <th>Nghe được</th>
          <th>Nhãn nội dung</th>
          <th>Score</th>
          <th>Tóm tắt</th>
        </tr>
      </thead>
      <tbody>{segment_rows}</tbody>
    </table>
  </section>
</main>
</body>
</html>
"""


def _transcribe_with_available_model(
    audio_path: Path,
    status: list[str],
) -> list[tuple[float, float, str]]:
    model_name = os.environ.get("DETECT_EVERYTHING_WHISPER_MODEL", "base")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        pass
    else:
        try:
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            segments, _info = model.transcribe(str(audio_path), vad_filter=True)
            return [
                (float(segment.start), float(segment.end), segment.text.strip())
                for segment in segments
                if segment.text.strip()
            ]
        except Exception as exc:
            status.append(f"faster-whisper chưa chạy được: {exc}")

    try:
        import whisper
    except ImportError:
        status.append(
            "Chưa cài faster-whisper hoặc whisper nên chưa thể chuyển lời nói thành chữ."
        )
        return []

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(str(audio_path))
    except Exception as exc:
        status.append(f"whisper chưa chạy được: {exc}")
        return []

    return [
        (
            float(segment.get("start", 0.0)),
            float(segment.get("end", 0.0)),
            str(segment.get("text", "")).strip(),
        )
        for segment in result.get("segments", [])
        if str(segment.get("text", "")).strip()
    ]


def _classify_speech_text(text_detector: TextFileDetector, text: str) -> tuple[str, float]:
    labeled_segments = text_detector.classify_text(text)
    if not labeled_segments:
        return "unlabeled", 0.0

    best_segment = max(labeled_segments, key=lambda segment: segment.score)
    return best_segment.label, best_segment.score


def _summarize_text(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= 160:
        return clean
    return f"{clean[:157].rstrip()}..."


def _count_rows(counts: dict[str, int]) -> str:
    if not counts:
        return '<tr><td class="muted">Không có dữ liệu</td><td>0</td></tr>'

    return "\n".join(
        f"<tr><td>{escape(name)}</td><td>{count}</td></tr>"
        for name, count in sorted(counts.items())
    )


def _video_has_audio(video_path: Path) -> bool:
    if shutil.which("ffprobe") is None:
        return True

    result = _run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
            str(video_path),
        ]
    )
    return "audio" in result.stdout.lower()


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _format_time(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, second = divmod(total_seconds, 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}"


def _report_to_json(report: AudioVideoReport) -> dict[str, object]:
    data = asdict(report)
    data["speech_segments"] = [asdict(segment) for segment in report.speech_segments]
    return data
