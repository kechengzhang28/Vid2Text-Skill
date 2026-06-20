import pathlib

from vid2text import utils


def test_exception_hierarchy():
    assert issubclass(utils.UserError, utils.Vid2TextError)
    assert issubclass(utils.DependencyError, utils.Vid2TextError)
    assert issubclass(utils.ModelError, utils.Vid2TextError)


def test_download_result_defaults():
    r = utils.DownloadResult(
        video_id="BV1xx",
        audio_path=pathlib.Path("/tmp/a.wav"),
        duration_sec=12.3,
    )
    assert r.video_id == "BV1xx"
    assert isinstance(r.audio_path, pathlib.Path)
