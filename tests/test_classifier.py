from organizer.core.classifier import classify
from organizer.core.config import DEFAULT_CATEGORIES, REVIEW_FOLDER_NAME


def test_every_default_extension_is_classified():
    for category, extensions in DEFAULT_CATEGORIES.items():
        for ext in extensions:
            assert classify(f"file{ext}", DEFAULT_CATEGORIES) == category


def test_case_insensitive():
    assert classify("Photo.JPG", DEFAULT_CATEGORIES) == "Images"
    assert classify("REPORT.PDF", DEFAULT_CATEGORIES) == "Documents"


def test_compound_extension_tar_gz():
    assert classify("backup.tar.gz", DEFAULT_CATEGORIES) == "Archives"


def test_compound_extension_prefers_longest_match():
    # backup.tar.gz should match ".tar.gz" (Archives), not misfire on ".gz" alone
    assert classify("archive.tar.gz", DEFAULT_CATEGORIES) == "Archives"
    assert classify("plain.gz", DEFAULT_CATEGORIES) == "Archives"


def test_unknown_extension_goes_to_review():
    assert classify("weird.xyz123", DEFAULT_CATEGORIES) == REVIEW_FOLDER_NAME


def test_no_extension_goes_to_review():
    assert classify("README", DEFAULT_CATEGORIES) == REVIEW_FOLDER_NAME


def test_hidden_dotfile_goes_to_review():
    assert classify(".gitignore", DEFAULT_CATEGORIES) == REVIEW_FOLDER_NAME


def test_custom_categories_override_defaults():
    custom = {"Notes": [".note"]}
    assert classify("idea.note", custom) == "Notes"
    assert classify("idea.pdf", custom) == REVIEW_FOLDER_NAME
