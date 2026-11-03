"""Tests for required documentation and local links."""

from pathlib import Path
import tempfile
import unittest

from ai.quality.qualitylib.docs import validate_docs


POLICY = {
    "required_docs": ["README.md", "docs/STANDARD.md"],
    "required_scripts": ["ai/quality/quality.py"],
}


def create_docs(root: Path) -> None:
    """Create a minimal documentation fixture."""
    (root / "docs").mkdir(parents=True)
    (root / "ai" / "quality").mkdir(parents=True)
    (root / "README.md").write_text(
        "# Project\n\n[Standard](docs/STANDARD.md)\n",
        encoding="utf-8",
    )
    (root / "docs" / "STANDARD.md").write_text("# Standard\n", encoding="utf-8")
    (root / "ai" / "quality" / "quality.py").write_text("", encoding="utf-8")


class DocumentationValidationTests(unittest.TestCase):
    """SPEC-001 AC-001 documentation entry and link cases."""

    def test_required_docs_and_local_links_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_docs(root)

            result = validate_docs(root, POLICY)

            self.assertTrue(result.passed, result.issues)
            self.assertEqual(result.links_checked, 1)

    def test_broken_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_docs(root)
            (root / "README.md").write_text(
                "# Project\n\n[Missing](docs/MISSING.md)\n",
                encoding="utf-8",
            )

            result = validate_docs(root, POLICY)

            self.assertFalse(result.passed)
            self.assertTrue(any("MISSING.md" in issue for issue in result.issues))

    def test_external_links_and_code_examples_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_docs(root)
            (root / "docs" / "STANDARD.md").write_text(
                "[Web](https://example.com)\n\n"
                "```markdown\n[Example](not-real.md)\n```\n",
                encoding="utf-8",
            )

            result = validate_docs(root, POLICY)

            self.assertTrue(result.passed, result.issues)

    def test_non_utf8_markdown_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_docs(root)
            (root / "docs" / "STANDARD.md").write_bytes(b"\xff\xfe")

            result = validate_docs(root, POLICY)

            self.assertFalse(result.passed)
            self.assertTrue(any("UTF-8" in issue for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
