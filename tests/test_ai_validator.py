from organizer.ai.validator import validate_recommendation

VALID = {
    "suggested_filename": "AWS-Invoice-2026-08.pdf",
    "top_level_category": "Documents",
    "suggested_subfolder": "Finance/Invoices",
    "confidence": 0.94,
    "reason": "Looks like an AWS invoice from August 2026.",
    "requires_review": True,
}


def test_valid_recommendation_passes(tmp_dest):
    result = validate_recommendation(VALID, "invoice_scan_001.pdf", tmp_dest, confidence_threshold=0.6)
    assert result.valid
    assert result.recommendation.relative_destination == "Documents/Finance/Invoices"


def test_malformed_json_missing_fields_fails(tmp_dest):
    result = validate_recommendation({"suggested_filename": "x.pdf"}, "x.pdf", tmp_dest)
    assert not result.valid
    assert result.errors


def test_wrong_field_types_fail(tmp_dest):
    bad = dict(VALID, confidence="high")  # should be a number
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_extension_must_be_preserved(tmp_dest):
    bad = dict(VALID, suggested_filename="AWS-Invoice-2026-08.exe")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid
    assert any("extension" in e for e in result.errors)


def test_absolute_path_rejected(tmp_dest):
    bad = dict(VALID, suggested_filename="/etc/passwd.pdf")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_path_traversal_in_subfolder_rejected(tmp_dest):
    bad = dict(VALID, suggested_subfolder="../../etc")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_path_traversal_in_filename_rejected(tmp_dest):
    bad = dict(VALID, suggested_filename="../../../etc/passwd.pdf")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_reserved_windows_name_rejected(tmp_dest):
    for reserved in ("CON", "con", "COM1", "LPT9", "NUL"):
        bad = dict(VALID, suggested_filename=f"{reserved}.pdf")
        result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
        assert not result.valid, f"{reserved} should have been rejected"


def test_invalid_windows_characters_rejected(tmp_dest):
    bad = dict(VALID, suggested_filename="in:valid?.pdf")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_excessive_filename_length_rejected(tmp_dest):
    bad = dict(VALID, suggested_filename=("a" * 300) + ".pdf")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_confidence_out_of_range_rejected(tmp_dest):
    bad = dict(VALID, confidence=1.5)
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid


def test_low_confidence_forces_requires_review(tmp_dest):
    low = dict(VALID, confidence=0.2, requires_review=False)
    result = validate_recommendation(low, "invoice_scan_001.pdf", tmp_dest, confidence_threshold=0.6)
    assert result.valid
    assert result.recommendation.requires_review is True


def test_never_overwrites_existing_file(tmp_dest):
    existing_dir = tmp_dest / "Documents" / "Finance" / "Invoices"
    existing_dir.mkdir(parents=True)
    (existing_dir / "AWS-Invoice-2026-08.pdf").write_text("already here")

    result = validate_recommendation(VALID, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid
    assert any("already exists" in e for e in result.errors)


def test_resolved_destination_cannot_escape_root(tmp_dest):
    bad = dict(VALID, top_level_category="..", suggested_subfolder="..")
    result = validate_recommendation(bad, "invoice_scan_001.pdf", tmp_dest)
    assert not result.valid
