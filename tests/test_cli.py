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
    assert "extracted_events" in output
    assert "source_reliability" in output


def test_cli_fetch_news_output_format(tmp_path, capsys):
    news_file = tmp_path / "news.jsonl"
    news_file.write_text(
        '{"headline":"NVIDIA receives upgrade","text":"NVIDIA was upgraded after strong demand.","source":"news"}\n',
        encoding="utf-8",
    )

    exit_code = main([str(news_file), "--fetch-news", "--model", "lexicon", "--backtest"])

    captured = capsys.readouterr()
    lines = [json.loads(line) for line in captured.out.splitlines()]
    assert exit_code == 0
    assert lines[0]["event"]["ticker"] == "NVDA"
    assert "extracted_events" in lines[0]
    assert "backtest" in lines[-1]


def test_cli_writes_output_file(tmp_path, capsys):
    input_file = tmp_path / "events.jsonl"
    output_file = tmp_path / "results.jsonl"
    input_file.write_text(
        '{"counterparty":"Apple","ticker":"AAPL","text":"Apple is stable.","source":"news"}\n',
        encoding="utf-8",
    )

    exit_code = main([str(input_file), "--output", str(output_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    row = json.loads(output_file.read_text(encoding="utf-8"))
    assert row["event"]["ticker"] == "AAPL"
    assert "score" in row
