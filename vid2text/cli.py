import sys

sys.dont_write_bytecode = True

import tempfile
from pathlib import Path

import click

from . import __version__, asr, downloader, transcoder
from .errors import Vid2TextError


@click.command()
@click.argument("url", required=False)
@click.option("--version", "show_version", is_flag=True, default=False, help="显示版本")
def main_entry(url: str, show_version: bool) -> None:
    """从 B站视频链接提取音频并转写为纯文本。"""
    if show_version:
        click.echo(f"vid2text {__version__}")
        return
    if not url:
        click.echo("使用: vid2text <B站链接或BV号>", err=True)
        sys.exit(1)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            audio = downloader.download(url, workdir)
            wav = transcoder.transcode(audio, workdir)
            text = asr.transcribe(wav)
        click.echo(text)
    except Vid2TextError as e:
        click.echo(str(e), err=True)
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main_entry()
