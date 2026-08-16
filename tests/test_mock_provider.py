from organizer.ai.mock_provider import MockProvider
from organizer.ai.validator import validate_recommendation


def test_mock_provider_never_sends_content_externally():
    assert MockProvider().sends_content_externally is False


def test_mock_provider_output_passes_validator(tmp_dest):
    provider = MockProvider()
    raw = provider.suggest("some text content", "my_report_final.pdf")
    result = validate_recommendation(raw, "my_report_final.pdf", tmp_dest)
    assert result.valid


def test_mock_provider_forced_malformed_response_fails_validation(tmp_dest):
    provider = MockProvider(force_response={"suggested_filename": "only_this_field.pdf"})
    raw = provider.suggest("content", "file.pdf")
    result = validate_recommendation(raw, "file.pdf", tmp_dest)
    assert not result.valid


def test_mock_provider_low_confidence(tmp_dest):
    provider = MockProvider(confidence=0.1)
    raw = provider.suggest("content", "file.pdf")
    result = validate_recommendation(raw, "file.pdf", tmp_dest, confidence_threshold=0.6)
    assert result.valid
    assert result.recommendation.requires_review is True
