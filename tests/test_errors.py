import pytest

from vid2text.errors import (
    Vid2TextError,
    UserError,
    NetworkError,
    TranscodeError,
    ModelError,
)


def test_base_exit_code_is_two():
    assert Vid2TextError().exit_code == 2


@pytest.mark.parametrize(
    "exc_cls, expected",
    [
        (UserError, 1),
        (NetworkError, 2),
        (TranscodeError, 2),
        (ModelError, 2),
    ],
)
def test_subclass_exit_codes(exc_cls, expected):
    assert exc_cls("msg").exit_code == expected


def test_subclasses_inherit_base():
    assert issubclass(UserError, Vid2TextError)
    assert issubclass(NetworkError, Vid2TextError)
