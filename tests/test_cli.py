import json

from counterparty_sentiment.cli import main


def test_cli_emits_jsonl_for_file(tmp_path, capsys):
    input_file = tmp_path / "events.jsonl"
    input_file.write_text(
        '{"counterparty":"Acme","text":"Acme is stable and compliant.","source":"news"}\n',
        encoding="utf-8",
    )

    exit_code = main([str(input_file), "--include-snapshot"])

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert exit_code == 0
    assert output["label"] == "positive"
    assert output["snapshot"]["counterparty"] == "Acme"
