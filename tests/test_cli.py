from click.testing import CliRunner

from vid2text.cli import main_entry
from vid2text.errors import NetworkError, UserError


def test_help_shows_usage():
    result = CliRunner().invoke(main_entry, ["--help"])
    assert result.exit_code == 0
    assert "转写" in result.output
    assert "URL" in result.output


def test_happy_path_outputs_text(monkeypatch):
    def fake_download(url, d):
        p = d / "a.m4a"
        p.write_bytes(b"x")
        return p

    monkeypatch.setattr("vid2text.cli.downloader.download", fake_download)
    monkeypatch.setattr("vid2text.cli.transcoder.transcode", lambda a, d: a)
    monkeypatch.setattr("vid2text.cli.asr.transcribe", lambda w: "转写结果")

    result = CliRunner().invoke(main_entry, ["BV1wDEK6MEM2"])

    assert result.exit_code == 0
    assert "转写结果" in result.output


def test_user_error_exits_one(monkeypatch):
    def boom(url, d):
        raise UserError("无效链接")
    monkeypatch.setattr("vid2text.cli.downloader.download", boom)

    result = CliRunner().invoke(main_entry, ["not-a-bvid"])

    assert result.exit_code == 1
    assert "无效链接" in result.output


def test_network_error_exits_two(monkeypatch):
    def boom(url, d):
        raise NetworkError("网络失败")
    monkeypatch.setattr("vid2text.cli.downloader.download", boom)

    result = CliRunner().invoke(main_entry, ["BV1wDEK6MEM2"])

    assert result.exit_code == 2
    assert "网络失败" in result.output
