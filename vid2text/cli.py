from __future__ import annotations

import json
import pathlib
import sys
import typing

import click

from vid2text import __version__, utils
from vid2text.cache import Cache
from vid2text.pipeline import run as _pipeline_run
from vid2text.pipeline import transcribe_file as _pipeline_transcribe_file

CACHE_ROOT = pathlib.Path.home() / ".vid2text" / "cache"

_EXIT_CODE: dict[type[utils.Vid2TextError], int] = {
    utils.UserError: 1,
    utils.DependencyError: 2,
    utils.ModelError: 2,
}

_MODEL_NAMES: dict[str, str] = {
    "paraformer": "Paraformer-Large",
    "sensevoice": "SenseVoice-Small",
}


def _run_pipeline(
    url: str,
    *,
    model_alias: str,
    fmt: str,
    language: str,
    no_cache: bool,
    cache_root: pathlib.Path,
) -> utils.RecognitionResult:
    return _pipeline_run(
        url,
        model_alias=model_alias,
        format=fmt,
        language=language,
        no_cache=no_cache,
        cache_root=cache_root,
    )


def _transcribe_pipeline(
    audio_path: pathlib.Path,
    *,
    model_alias: str,
    fmt: str,
    language: str,
    no_cache: bool,
    cache_root: pathlib.Path,
) -> utils.RecognitionResult:
    return _pipeline_transcribe_file(
        audio_path,
        model_alias=model_alias,
        format=fmt,
        language=language,
        no_cache=no_cache,
        cache_root=cache_root,
    )


def _report(err: utils.Vid2TextError) -> typing.NoReturn:
    code = 1
    for exc_type, exit_code in _EXIT_CODE.items():
        if isinstance(err, exc_type):
            code = exit_code
            break
    click.echo(f"[error] {err}", err=True)
    sys.exit(code)


def _render_txt(result: utils.RecognitionResult) -> str:
    return result.text


def _render_json(result: utils.RecognitionResult) -> str:
    return json.dumps(
        {
            "meta": {
                "model": _MODEL_NAMES.get(result.model_alias, result.model_alias),
                "language": result.language,
                "duration_sec": result.duration_sec,
                "video_id": result.video_id,
                "source_url": result.source_url,
            },
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text, "confidence": s.confidence}
                for s in result.segments
            ],
            "text": result.text,
        },
        ensure_ascii=False,
        indent=2,
    )


def _render_output(result: utils.RecognitionResult, fmt: str) -> str:
    if fmt == "json":
        return _render_json(result)
    return _render_txt(result)


def _emit(result: utils.RecognitionResult, fmt: str, output: pathlib.Path | None) -> None:
    full = _render_output(result, fmt)
    if output is not None:
        output.write_text(full, encoding="utf-8")
        word_count = len(result.text)
        click.echo(f"{output.resolve()}\t{word_count}\t{result.duration_sec:.1f}")
    else:
        click.echo(full)


@click.group()
@click.version_option(__version__, prog_name="vid2text")
def main() -> None:
    """vid2text — 视频语音转文字 CLI"""


@main.command("run")
@click.argument("url")
@click.option("-o", "--output", type=click.Path(path_type=pathlib.Path))
@click.option(
    "-m", "--model", type=click.Choice(["paraformer", "sensevoice"]), default="paraformer"
)
@click.option("-f", "--format", "fmt", type=click.Choice(["txt", "json"]), default="txt")
@click.option(
    "-l",
    "--language",
    type=click.Choice(["auto", "zh", "en", "ja", "ko", "yue"]),
    default="auto",
)
@click.option("--keep-audio", is_flag=True, default=False)
@click.option("--no-cache", is_flag=True, default=False)
@click.option("-v", "--verbose", count=True)
def run_cmd(
    url: str,
    output: pathlib.Path | None,
    model: str,
    fmt: str,
    language: str,
    keep_audio: bool,
    no_cache: bool,
    verbose: int,
):
    """下载视频音频并转写"""
    try:
        result = _run_pipeline(
            url,
            model_alias=model,
            fmt=fmt,
            language=language,
            no_cache=no_cache,
            cache_root=CACHE_ROOT,
        )
        _emit(result, fmt, output)
    except utils.Vid2TextError as e:
        _report(e)


@main.command("transcribe")
@click.argument("audio_file", type=click.Path(path_type=pathlib.Path))
@click.option(
    "-m", "--model", type=click.Choice(["paraformer", "sensevoice"]), default="paraformer"
)
@click.option("-f", "--format", "fmt", type=click.Choice(["txt", "json"]), default="txt")
@click.option(
    "-l",
    "--language",
    type=click.Choice(["auto", "zh", "en", "ja", "ko", "yue"]),
    default="auto",
)
@click.option("-o", "--output", type=click.Path(path_type=pathlib.Path))
@click.option("--no-cache", is_flag=True, default=False)
def transcribe_cmd(
    audio_file: pathlib.Path,
    model: str,
    fmt: str,
    language: str,
    output: pathlib.Path | None,
    no_cache: bool,
):
    """转写本地音频文件"""
    try:
        if not audio_file.exists():
            raise utils.UserError(f"文件不存在: {audio_file}")
        result = _transcribe_pipeline(
            audio_file,
            model_alias=model,
            fmt=fmt,
            language=language,
            no_cache=no_cache,
            cache_root=CACHE_ROOT,
        )
        _emit(result, fmt, output)
    except utils.Vid2TextError as e:
        _report(e)


@main.group()
def cache() -> None:
    """缓存管理"""


@cache.command("list")
def cache_list() -> None:
    c = Cache(CACHE_ROOT)
    entries = c.list_entries()
    if entries:
        for e in entries:
            click.echo(e)
    else:
        click.echo("(empty)")


@cache.command("clear")
def cache_clear() -> None:
    c = Cache(CACHE_ROOT)
    c.clear()
    click.echo("缓存已清空")
