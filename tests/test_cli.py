import json
import struct

import click.testing
import pytest

from vid2text import cli, utils


@pytest.fixture
def sample_wav(tmp_path):
    p = tmp_path / "sample.wav"
    header = bytearray(44)
    header[0:4] = b"RIFF"
    header[8:12] = b"WAVE"
    header[12:16] = b"fmt "
    struct.pack_into("<I", header, 16, 16)
    struct.pack_into("<H", header, 20, 1)
    struct.pack_into("<H", header, 22, 1)
    struct.pack_into("<I", header, 24, 16000)
    struct.pack_into("<I", header, 28, 32000)
    struct.pack_into("<H", header, 32, 2)
    struct.pack_into("<H", header, 34, 16)
    header[36:40] = b"data"
    struct.pack_into("<I", header, 40, 0)
    p.write_bytes(bytes(header))
    return p


class TestCliSkeleton:
    def test_version_flag(self):
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["--version"])
        assert res.exit_code == 0
        assert "vid2text" in res.output

    def test_invalid_url_exits_1(self, monkeypatch):
        def fake_run(*a, **k):
            raise utils.UserError("无效 URL")

        monkeypatch.setattr(cli, "_run_pipeline", fake_run)
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "not a url"])
        assert res.exit_code == 1


class TestRunCommand:
    def _patch(self, monkeypatch, result):
        monkeypatch.setattr(cli, "_run_pipeline", lambda *a, **k: result)

    def _sample_result(self):
        return utils.RecognitionResult(
            model_alias="paraformer",
            language="zh",
            duration_sec=4.2,
            segments=[
                utils.Segment(0.0, 2.0, "你好", 0.97),
                utils.Segment(2.0, 4.2, "世界", 0.95),
            ],
            text="你好世界",
            video_id="BV1xx411c7mD",
            source_url="https://www.bilibili.com/video/BV1xx411c7mD",
            content_hash="abc123",
        )

    def test_run_txt_stdout(self, monkeypatch):
        self._patch(monkeypatch, self._sample_result())
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "https://www.bilibili.com/video/BV1xx411c7mD"])
        assert res.exit_code == 0
        assert "你好世界" in res.output

    def test_run_json_stdout(self, monkeypatch):
        self._patch(monkeypatch, self._sample_result())
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, [
            "run", "https://www.bilibili.com/video/BV1xx411c7mD", "-f", "json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "meta" in data
        assert "segments" in data
        assert "text" in data
        assert data["meta"]["model"] == "Paraformer-Large"

    def test_run_output_file_writes_full_result(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, self._sample_result())
        out = tmp_path / "out.txt"
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, [
            "run", "https://www.bilibili.com/video/BV1xx411c7mD", "-o", str(out),
        ])
        assert res.exit_code == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "你好世界" in content

    def test_run_output_stdout_summary(self, monkeypatch, tmp_path):
        self._patch(monkeypatch, self._sample_result())
        out = tmp_path / "out.txt"
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, [
            "run", "https://www.bilibili.com/video/BV1xx411c7mD", "-o", str(out),
        ])
        assert res.exit_code == 0
        parts = res.output.strip().split("\t")
        assert len(parts) == 3
        assert str(out.resolve()) in parts[0]


class TestTranscribeCommand:
    def _patch(self, monkeypatch, result):
        monkeypatch.setattr(cli, "_transcribe_pipeline", lambda *a, **k: result)

    def _sample_result(self):
        return utils.RecognitionResult(
            model_alias="sensevoice",
            language="en",
            duration_sec=3.0,
            segments=[utils.Segment(0.0, 3.0, "hello", 0.99)],
            text="hello",
        )

    def test_transcribe_txt_stdout(self, monkeypatch, sample_wav):
        self._patch(monkeypatch, self._sample_result())
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["transcribe", str(sample_wav)])
        assert res.exit_code == 0
        assert "hello" in res.output

    def test_transcribe_file_not_found(self):
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["transcribe", "/nonexistent/file.wav"])
        assert res.exit_code == 1


class TestCacheCommands:
    def test_cache_list_empty(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cli, "CACHE_ROOT", tmp_path / "cache")
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["cache", "list"])
        assert res.exit_code == 0

    def test_cache_clear(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cli, "CACHE_ROOT", tmp_path / "cache")
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["cache", "clear"])
        assert res.exit_code == 0
