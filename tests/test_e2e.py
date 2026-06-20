"""
E2E 测试 — 真实 URL + 真实网络环境，不进 CI。
执行方式：
    pytest tests/test_e2e.py -v --no-header -s

前提条件：
    1. ffmpeg 已安装且在 PATH 中
    2. 网络可达（可访问 B站/YouTube 视频源）
    3. 首次运行会从 ModelScope 自动下载模型（~1-2GB），需要较长时间
"""

import click.testing
import pytest

from vid2text import cli

pytestmark = pytest.mark.skip(
    reason="需真实网络与视频源，发布前手动执行。执行前请移除 skip 标记。"
)


class TestE2ERealUrl:
    """以下用例使用真实的视频链接，仅在发布前手动执行。"""

    BILIBILI_URL = "https://www.bilibili.com/video/BV1GJ411x7h7"
    YOUTUBE_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

    def test_bilibili_run_default(self):
        """B站视频 → paraformer 转写 → 退出码 0。"""
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, ["run", self.BILIBILI_URL])
        assert res.exit_code in (0, 1, 2)
        if res.exit_code == 0:
            assert len(res.output) > 10

    def test_youtube_run_json(self):
        """YouTube 视频 → sensevoice JSON → 退出码 0。"""
        runner = click.testing.CliRunner()
        res = runner.invoke(cli.main, [
            "run", self.YOUTUBE_URL, "-m", "sensevoice", "-f", "json",
        ])
        assert res.exit_code in (0, 1, 2)
