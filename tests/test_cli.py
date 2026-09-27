import json
import os
import subprocess
import sys


def run_cli(tmp_path, *args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "article_audio", "--config-dir", str(tmp_path / "config"), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env={
            key: value
            for key, value in os.environ.items()
            if key
            not in (
                "GEMINI_API_KEY",
                "R2_ACCOUNT_ID",
                "R2_ACCESS_KEY_ID",
                "R2_SECRET_ACCESS_KEY",
                "R2_BUCKET",
            )
        },
    )


def test_plan_works_without_keys(tmp_path):
    source = tmp_path / "article.txt"
    source.write_text("A full article supplied by the bot.")
    result = run_cli(tmp_path, "plan", str(source))
    assert result.returncode == 0
    assert json.loads(result.stdout)["words"] == 7


def test_secure_stdin_import_and_missing_credential_error(tmp_path):
    imported = run_cli(
        tmp_path, "auth", "import-json", stdin='{"GEMINI_API_KEY":"unique-private-value"}'
    )
    assert imported.returncode == 0
    assert "unique-private-value" not in imported.stdout + imported.stderr
    status = run_cli(tmp_path, "auth", "status")
    assert "unique-private-value" not in status.stdout + status.stderr
    assert json.loads(status.stdout)["gemini"]["missing"] == []
    source = tmp_path / "article.txt"
    source.write_text("Hello world")
    missing = run_cli(tmp_path / "another-user", "generate", str(source))
    assert missing.returncode == 2
    assert json.loads(missing.stdout)["error"]["code"] == "credentials_required"
