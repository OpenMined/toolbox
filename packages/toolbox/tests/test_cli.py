from toolbox.cli.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0, result.exception
    assert "Toolbox version" in result.output
