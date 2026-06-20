import pathlib
import struct
import wave


def generate(wav_dir: pathlib.Path, duration_sec: float = 1.0) -> pathlib.Path:
    wav_dir.mkdir(parents=True, exist_ok=True)
    path = wav_dir / "sample.wav"
    sample_rate = 16000
    num_samples = int(sample_rate * duration_sec)

    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        for i in range(num_samples):
            frame = struct.pack("<h", int(16000 * (i % 200) / 200))
            w.writeframes(frame)
    return path


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parent.parent
    p = generate(root / "tests" / "fixtures")
    print(f"Generated: {p}")
