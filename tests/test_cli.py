from click.testing import CliRunner

from vid2text.cli import main_entry


def test_help_shows_usage():
    result = CliRunner().invoke(main_entry, ["--help"])
    assert result.exit_code == 0
    assert "转写" in result.output
    assert "URL" in result.output
