from pathlib import Path


def transcribe_media(path: str) -> dict[str, str]:
    input_path = Path(path)
    source_path = input_path

    if input_path.suffix.lower() in {".mp4", ".mov", ".mkv"}:
        import ffmpeg

        wav_path = input_path.with_suffix(".wav")
        ffmpeg.input(str(input_path)).output(str(wav_path), ac=1, ar=16000).overwrite_output().run(quiet=True)
        source_path = wav_path

    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(source_path), vad_filter=True)
    transcript = " ".join(segment.text.strip() for segment in segments)
    return {"path": path, "transcript": transcript}
