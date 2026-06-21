import sys
import tempfile
from pathlib import Path

import click

from . import asr, downloader, transcoder
from .errors import Vid2TextError


@click.command()
@click.argument("url")
def main_entry(url: str) -> None:
    """从 B站视频链接提取音频并转写为纯文本。"""
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
