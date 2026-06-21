import os
from pathlib import Path

from .errors import ModelError, NetworkError

os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("FUNASR_DEVICE", "cpu")

_PARAFORMER = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-onnx"
_VAD = "iic/speech_fsmn_vad_zh-cn-16k-common-onnx"
_PUNC = "iic/punc_ct-transformer_zh-cn-common-vocab272727-onnx"
_REVISION = "v2.0.5"

_models: dict = {}


def _ensure_models() -> None:
    if _models:
        return
    try:
        from modelscope.hub import snapshot_download
        from funasr_onnx import Paraformer, Fsmn_vad, CT_Transformer
    except ImportError as e:
        raise ModelError(f"加载 ASR 依赖失败: {e}") from e
    try:
        para_dir = snapshot_download(_PARAFORMER, revision=_REVISION)
        vad_dir = snapshot_download(_VAD, revision=_REVISION)
        punc_dir = snapshot_download(_PUNC, revision=_REVISION)
    except Exception as e:
        raise NetworkError(f"模型下载失败: {e}") from e
    try:
        _models["paraformer"] = Paraformer(
            para_dir, batch_size=1, device_id=-1, quantize=True
        )
        _models["vad"] = Fsmn_vad(vad_dir)
        _models["punc"] = CT_Transformer(punc_dir)
    except Exception as e:
        raise ModelError(f"模型加载失败: {e}") from e


def transcribe(wav_path: Path) -> str:
    _ensure_models()
    try:
        result = _models["paraformer"]([str(wav_path)])
        parts = []
        for item in result:
            if isinstance(item, dict) and "preds" in item:
                pred = item["preds"]
                parts.append(pred[0] if isinstance(pred, tuple) else pred)
            else:
                parts.append(str(item))
        raw = "".join(parts)
        text, _ = _models["punc"](raw)
        return text.strip()
    except Exception as e:
        raise ModelError(f"ASR 推理失败: {e}") from e
