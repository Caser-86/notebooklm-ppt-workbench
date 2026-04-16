from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceBundle:
    prompt: str
    urls: list[str]
    file_paths: list[str]
    file_texts: list[dict[str, str]]
    image_paths: list[str]
    audio_paths: list[str]
    video_paths: list[str]


def _normalize_path(path: Path) -> str:
    return path.as_posix()


def build_source_bundle(
    prompt: str,
    urls: list[str],
    file_paths: list[Path],
    image_paths: list[Path],
    audio_paths: list[Path],
    video_paths: list[Path],
) -> SourceBundle:
    file_texts = [{"path": _normalize_path(path), "text": path.read_text(encoding="utf-8")} for path in file_paths]
    return SourceBundle(
        prompt=prompt,
        urls=urls,
        file_paths=[_normalize_path(path) for path in file_paths],
        file_texts=file_texts,
        image_paths=[_normalize_path(path) for path in image_paths],
        audio_paths=[_normalize_path(path) for path in audio_paths],
        video_paths=[_normalize_path(path) for path in video_paths],
    )


def summarize_source_bundle(bundle: SourceBundle) -> str:
    def count_label(count: int, singular: str, plural: str) -> str:
        return f"{count} {singular if count == 1 else plural}"

    parts = [
        count_label(len(bundle.urls), "url", "urls"),
        count_label(len(bundle.file_paths), "file", "files"),
        count_label(len(bundle.image_paths), "image", "images"),
        count_label(len(bundle.audio_paths), "audio", "audio"),
        count_label(len(bundle.video_paths), "video", "video"),
    ]
    return ", ".join(parts)
