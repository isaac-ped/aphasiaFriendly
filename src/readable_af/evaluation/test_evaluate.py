from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr, ValidationError

from evaluation import evaluate as evaluator


def write_article(path: Path, *, title: str = "Title", abstract: str = "Abstract") -> None:
    path.write_text(
        json.dumps({"title": title, "abstract": abstract}),
        encoding="utf-8",
    )


def test_load_article_accepts_blank_title(tmp_path: Path) -> None:
    article_path = tmp_path / "summary.json"
    write_article(article_path, title="", abstract="A useful summary.")

    article = evaluator.load_article(article_path)

    assert article.title == ""
    assert article.abstract == "A useful summary."


@pytest.mark.parametrize(
    "contents",
    [
        "not json",
        json.dumps({"title": "Missing abstract"}),
        json.dumps({"title": 123, "abstract": "Text"}),
        json.dumps({"title": "Title", "abstract": "   "}),
    ],
)
def test_load_article_rejects_invalid_json(tmp_path: Path, contents: str) -> None:
    article_path = tmp_path / "article.json"
    article_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid article JSON"):
        evaluator.load_article(article_path)


def test_evaluate_uses_langchain_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rating = evaluator.SummaryRating(
        accuracy=8,
        coverage=7,
        simplicity=9,
        clarity=8,
    )
    captured: dict[str, Any] = {}

    class FakeStructuredModel:
        def invoke(self, messages: list[object]) -> evaluator.SummaryRating:
            captured["messages"] = messages
            return rating

    class FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured["model_kwargs"] = kwargs

        def with_structured_output(
            self, schema: type[evaluator.SummaryRating], *, method: str
        ) -> FakeStructuredModel:
            captured["schema"] = schema
            captured["method"] = method
            return FakeStructuredModel()

    monkeypatch.setattr(evaluator, "ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr(
        evaluator.Config,
        "get",
        lambda: SimpleNamespace(openai_api_key="test-key"),
    )

    result = evaluator.evaluate(
        evaluator.ArticleText(title="Original", abstract="Source facts"),
        evaluator.ArticleText(title="Simple", abstract="Simple facts"),
    )

    assert result is rating
    assert captured["schema"] is evaluator.SummaryRating
    assert captured["method"] == "json_schema"
    model_kwargs = captured["model_kwargs"]
    assert model_kwargs["model"] == evaluator.OPENAI_MODEL
    assert isinstance(model_kwargs["api_key"], SecretStr)
    assert model_kwargs["api_key"].get_secret_value() == "test-key"
    messages = captured["messages"]
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert "SOURCE TITLE:\nOriginal" in str(messages[1].content)
    assert "GENERATED ABSTRACT:\nSimple facts" in str(messages[1].content)


def test_create_model_uses_anthropic_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeChatAnthropic:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(evaluator, "ChatAnthropic", FakeChatAnthropic)
    monkeypatch.setattr(
        evaluator.Config,
        "get",
        lambda: SimpleNamespace(
            openai_api_key="openai-key",
            anthropic_api_key="anthropic-key",
        ),
    )

    evaluator.create_model("anthropic")

    assert captured["model_name"] == evaluator.ANTHROPIC_MODEL
    assert isinstance(captured["api_key"], SecretStr)
    assert captured["api_key"].get_secret_value() == "anthropic-key"


def test_create_model_requires_anthropic_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        evaluator.Config,
        "get",
        lambda: SimpleNamespace(
            openai_api_key="openai-key",
            anthropic_api_key=None,
        ),
    )

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        evaluator.create_model("anthropic")


def test_evaluate_rejects_untyped_result(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeStructuredModel:
        def invoke(self, messages: list[object]) -> dict[str, int]:
            return {"accuracy": 8}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            pass

        def with_structured_output(
            self, schema: type[evaluator.SummaryRating], *, method: str
        ) -> FakeStructuredModel:
            return FakeStructuredModel()

    monkeypatch.setattr(evaluator, "create_model", lambda provider: FakeChatOpenAI())

    with pytest.raises(RuntimeError, match="valid summary rating"):
        evaluator.evaluate(
            evaluator.ArticleText(title="Original", abstract="Source facts"),
            evaluator.ArticleText(title="Simple", abstract="Simple facts"),
        )


def test_summary_rating_enforces_score_bounds() -> None:
    with pytest.raises(ValidationError):
        evaluator.SummaryRating(
            accuracy=0,
            coverage=7,
            simplicity=9,
            clarity=8,
        )


@pytest.mark.parametrize("json_output", [False, True])
def test_main_prints_requested_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    json_output: bool,
) -> None:
    source_path = tmp_path / "summary.orig.json"
    summary_path = tmp_path / "summary.json"
    write_article(source_path, title="Original", abstract="Source facts")
    write_article(summary_path, title="", abstract="Simple facts")
    rating = evaluator.SummaryRating(
        accuracy=8,
        coverage=7,
        simplicity=9,
        clarity=8,
    )
    selected_provider = "anthropic" if json_output else "openai"
    captured: dict[str, object] = {}

    def fake_evaluate(
        source: evaluator.ArticleText,
        summary: evaluator.ArticleText,
        provider: evaluator.Provider,
    ) -> evaluator.SummaryRating:
        captured["provider"] = provider
        return rating

    monkeypatch.setattr(evaluator, "evaluate", fake_evaluate)
    arguments = [str(source_path), str(summary_path)]
    if json_output:
        arguments.extend(("--json", "--provider", selected_provider))

    assert evaluator.main(arguments) == 0
    assert captured["provider"] == selected_provider

    output = capsys.readouterr().out
    if json_output:
        assert json.loads(output) == rating.model_dump()
    else:
        assert "AphasiaFriendly Summary Evaluation" in output
        assert "Accuracy      8/10" in output