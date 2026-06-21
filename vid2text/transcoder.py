from pathlib import Path

import av

from .errors import TranscodeError


def transcode(audio_path: Path, output_dir: Path) -> Path:
    audio_path = Path(audio_path)
    if audio_path.suffix.lower() == ".wav":
        return audio_path

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / (audio_path.stem + ".wav")

    try:
        input_container = av.open(str(audio_path))
        audio_stream = input_container.streams.audio[0]

        output_container = av.open(str(out), "w")
        output_stream = output_container.add_stream("pcm_s16le", rate=16000, layout="mono")

        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000,
        )

        for frame in input_container.decode(audio=0):
            for resampled_frame in resampler.resample(frame):
                for packet in output_stream.encode(resampled_frame):
                    output_container.mux(packet)

        for packet in output_stream.encode():
            output_container.mux(packet)

        output_container.close()
        input_container.close()
    except Exception as e:
        raise TranscodeError(f"转码失败: {e}") from e

    return out
