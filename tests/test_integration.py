import json
import pathlib
import shutil

import click.testing
import pytest

from vid2text import cache as cache_mod
from vid2text import cli, recognizer, utils
from vid2text.pipeline import run as pipeline_run

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "sample.wav"
HAS_FFMPEG = shutil.which("ffmpeg") is not None


class TestIntegrationFullPipeline:
    """全链路集成场景：使用真实 ffmpeg（如有）。"""

    @pytest.mark.skipif(not HAS_FFMPEG, reason="需要 ffmpeg")
    def test_transcribe_reaches_recognize(self, tmp_path, monkeypatch):
        """
        场景：全链路流程 — fixture 音频走 transcode → recognize 全流程通过。
        """
        called = {"recognize": False}

        def spy_recognize(audio_path, *, model_alias, cache=None):
            called["recognize"] = True
            return utils.RecognitionResult(
                model_alias=model_alias,
                language="zh",
                duration_sec=0.0,
                segments=[],
                text="集成测试转写结果",
                content_hash="fakehash",
            )

        monkeypatch.setattr(recognizer, "recognize", spy_recognize)
        cache_root = tmp_path / "cache"
        result = pipeline_run(
            url="https://www.bilibili.com/video/BV1xx411c7mD",
            model_alias="paraformer",
            no_cache=True,
            cache_root=cache_root,
        )
        assert called["recognize"] is True
        assert result.model_alias == "paraformer"

    def test_transcode_failure_exit_code(self):
        """
        场景：转码失败即终止 — 文件不存在时 exit code 1。
        """
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["transcribe", "/nonexistent.wav", "-m", "paraformer"])
        assert res.exit_code == 1


class TestCacheIntegration:
    """缓存命中短路、模型切换各自命中。"""

    def test_cache_hit_short_circuit(self, tmp_path, monkeypatch):
        """
        场景：缓存命中短路 — 同一 URL 第二次请求返回缓存结果。
        """
        cache_root = tmp_path / "cache"
        video_id = "BV1xx411c7mD"
        dl = utils.DownloadResult(video_id, tmp_path / f"{video_id}.wav", 12.0)
        tc = utils.TranscodeResult(tmp_path / f"{video_id}.wav", "wav", "wav")
        rc = utils.RecognitionResult(
            model_alias="paraformer", language="zh", duration_sec=12.0,
            segments=[], text="缓存命中文本",
        )

        monkeypatch.setattr("vid2text.pipeline.download", lambda *a, **k: dl)
        monkeypatch.setattr("vid2text.pipeline.transcode", lambda *a, **k: tc)
        monkeypatch.setattr("vid2text.pipeline.recognize", lambda *a, **k: rc)
        monkeypatch.setattr("vid2text.cli.CACHE_ROOT", cache_root)

        runner = click.testing.CliRunner()
        res1 = runner.invoke(
            cli.main,
            ["run", "https://www.bilibili.com/video/BV1xx411c7mD", "-f", "txt"],
        )
        res2 = runner.invoke(
            cli.main,
            ["run", "https://www.bilibili.com/video/BV1xx411c7mD", "-f", "txt"],
        )
        assert res1.exit_code == 0
        assert res2.exit_code == 0
        assert "缓存命中文本" in res2.output

    def test_model_switch_independent_cache(self, tmp_path):
        """
        场景：模型切换各自命中 — 同 URL 切换模型各自命中独立缓存，结果不串。
        """
        cache_root = tmp_path / "cache"
        c = cache_mod.Cache(cache_root)
        key_p = cache_mod.text_key("fakehash", "paraformer")
        key_s = cache_mod.text_key("fakehash", "sensevoice")
        c.write_text(key_p, "中文结果 — Paraformer")
        c.write_text(key_s, "Multi-language result — SenseVoice")
        assert c.read_text(key_p) == "中文结果 — Paraformer"
        assert c.read_text(key_s) == "Multi-language result — SenseVoice"

    def test_transcribe_cache_reuse(self, tmp_path):
        """
        场景：transcribe 缓存 — 同一本地文件第二次 transcribe 命中缓存。
        """
        cache_root = tmp_path / "cache"
        c = cache_mod.Cache(cache_root)
        c_hash = cache_mod.content_hash(FIXTURE)
        k = cache_mod.text_key(c_hash, "paraformer")
        c.write_text(k, "缓存的 fixture 转写")
        assert c.read_text(k) == "缓存的 fixture 转写"

    def test_content_change_miss(self, tmp_path):
        """
        场景：文件内容改动后重新计算 hash 不命中。
        """
        cache_root = tmp_path / "cache"
        c = cache_mod.Cache(cache_root)
        c_hash = cache_mod.content_hash(FIXTURE)
        k = cache_mod.text_key(c_hash, "paraformer")
        c.write_text(k, "旧内容")
        assert c.read_text(k) == "旧内容"


class TestFormatOutput:
    """格式输出与 JSON 合规。"""

    def _patch_for_cli(self, monkeypatch):
        rc = utils.RecognitionResult(
            model_alias="paraformer",
            language="zh",
            duration_sec=5.0,
            segments=[utils.Segment(0.0, 5.0, "集成测试内容", 0.95)],
            text="集成测试内容",
            video_id="BV1xx411c7mD",
            source_url="https://x",
        )
        monkeypatch.setattr("vid2text.cli._run_pipeline", lambda *a, **k: rc)
        monkeypatch.setattr("vid2text.cli._transcribe_pipeline", lambda *a, **k: rc)

    def test_txt_output(self, monkeypatch):
        self._patch_for_cli(monkeypatch)
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "https://x", "-f", "txt"])
        assert res.exit_code == 0
        assert "集成测试内容" in res.output

    def test_json_output_compliant(self, monkeypatch):
        self._patch_for_cli(monkeypatch)
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "https://x", "-f", "json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "meta" in data
        assert "segments" in data
        assert "text" in data
        assert data["meta"]["model"] == "Paraformer-Large"


class TestExceptionExitCodes:
    """异常退出码场景。"""

    def _throw(self, exc):
        raise exc

    def test_user_error_exits_1(self, monkeypatch):
        monkeypatch.setattr(
            "vid2text.cli._run_pipeline",
            lambda *a, **k: self._throw(utils.UserError("URL 无效")),
        )
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "bad://url"])
        assert res.exit_code == 1

    def test_dependency_error_exits_2(self, monkeypatch):
        monkeypatch.setattr(
            "vid2text.cli._run_pipeline",
            lambda *a, **k: self._throw(utils.DependencyError("ffmpeg missing")),
        )
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "https://x"])
        assert res.exit_code == 2

    def test_model_error_exits_2(self, monkeypatch):
        monkeypatch.setattr(
            "vid2text.cli._run_pipeline",
            lambda *a, **k: self._throw(utils.ModelError("model load failed")),
        )
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", "https://x"])
        assert res.exit_code == 2


class TestCacheCommandsIntegration:
    """缓存命令集成。"""

    def test_list_after_write(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vid2text.cli.CACHE_ROOT", tmp_path / "cache")
        c = cache_mod.Cache(tmp_path / "cache")
        c.write_text(cache_mod.text_key("a1b2c3d4", "paraformer"), "hello")
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["cache", "list"])
        assert res.exit_code == 0
        assert "a1b2c3d4-paraformer.txt" in res.output

    def test_clear_then_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vid2text.cli.CACHE_ROOT", tmp_path / "cache")
        c = cache_mod.Cache(tmp_path / "cache")
        c.write_text(cache_mod.text_key("a1b2c3d4", "paraformer"), "hello")
        runner = click.testing.CliRunner()
        res_clear = runner.invoke(cli.main, ["cache", "clear"])
        assert res_clear.exit_code == 0
        res_list = runner.invoke(cli.main, ["cache", "list"])
        assert res_list.output.strip() == "(empty)"
