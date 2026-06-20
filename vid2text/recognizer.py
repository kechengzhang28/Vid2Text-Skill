from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing

from vid2text import utils
from vid2text.cache import Cache, content_hash, text_key

_log = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class ModelSpec:
    alias: str
    asr_id: str
    use_vad: bool
    use_punc: bool
    languages: tuple[str, ...]


_SPECS = {
    "paraformer": ModelSpec(
        alias="paraformer",
        asr_id="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        use_vad=True,
        use_punc=True,
        languages=("zh",),
    ),
    "sensevoice": ModelSpec(
        alias="sensevoice",
        asr_id="iic/Speech_SENSE_Voice_Small",
        use_vad=True,
        use_punc=True,
        languages=("zh", "en", "yue", "ja", "ko"),
    ),
}


def resolve_model(alias: str) -> ModelSpec:
    if alias not in _SPECS:
        raise utils.UserError(f"未知模型: {alias}")
    return _SPECS[alias]


def _load_auto_model(spec: ModelSpec) -> typing.Any:  # pyright: ignore[reportExplicitAny]
    from funasr import AutoModel

    return AutoModel(model=spec.asr_id, vad_kwargs={"max_single_segment_time": 60000})


def _result_from_output(
    output: list[dict[str, typing.Any]], spec: ModelSpec, c_hash: str  # pyright: ignore[reportExplicitAny]
) -> utils.RecognitionResult:
    segments: list[utils.Segment] = []
    for item in output:
        text = item.get("text", "")
        ts: list[list[int]] = item.get("timestamp", [[0, 0]])
        seg_start = ts[0][0] / 1000.0 if ts and ts[0] else 0.0
        seg_end = ts[-1][1] / 1000.0 if ts and ts[-1] else 0.0
        confidence = float(item.get("confidence", 0))
        segments.append(
            utils.Segment(start=seg_start, end=seg_end, text=text, confidence=confidence)
        )
    full_text = "".join(s.text for s in segments)
    duration = segments[-1].end if segments else 0.0
    return utils.RecognitionResult(
        model_alias=spec.alias,
        language=spec.languages[0],
        duration_sec=duration,
        segments=segments,
        text=full_text,
        content_hash=c_hash,
    )


def recognize(
    audio_path: pathlib.Path,
    *,
    model_alias: str,
    cache: Cache | None = None,
) -> utils.RecognitionResult:
    spec = resolve_model(model_alias)
    c_hash = content_hash(audio_path)
    key = text_key(c_hash, model_alias)

    if cache is not None:
        cached_text = cache.read_text(key)
        if cached_text is not None:
            return utils.RecognitionResult(
                model_alias=spec.alias,
                language=spec.languages[0],
                duration_sec=0.0,
                segments=[],
                text=cached_text,
                content_hash=c_hash,
            )

    try:
        model = _load_auto_model(spec)
        output: list[dict[str, typing.Any]] = model.generate(input=str(audio_path))
    except Exception as e:
        raise utils.ModelError(f"ASR 识别失败: {e}") from e

    result = _result_from_output(output, spec, c_hash)

    if cache is not None:
        cache.write_text(key, result.text)

    return result
