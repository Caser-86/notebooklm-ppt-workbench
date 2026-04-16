from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceBundle:
    prompt: str
    urls: list[str]
    file_texts: list[dict[str, str]]
    image_paths: list[str]
    audio_paths: list[str]
    video_paths: list[str]


def build_source_bundle(
    prompt: str,
    urls: list[str],
    file_paths: list[Path],
    image_paths: list[Path],
    audio_paths: list[Path],
    video_paths: list[Path],
) -> SourceBundle:
    file_texts = [{"path": str(path), "text": path.read_text(encoding="utf-8")} for path in file_paths]
    return SourceBundle(
        prompt=prompt,
        urls=urls,
        file_texts=file_texts,
        image_paths=[str(path) for path in image_paths],
        audio_paths=[str(path) for path in audio_paths],
        video_paths=[str(path) for path in video_paths],
    )
