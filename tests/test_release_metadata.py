"""Release metadata regressions; do not mistake the source version for a published release."""
import unittest
from importlib.metadata import version
from pathlib import Path

from contextbridge import __version__


class ReleaseMetadataTests(unittest.TestCase):
    def test_installed_distribution_matches_package_version(self):
        self.assertEqual(version("contextbridge-cli"), __version__)

    def test_changelog_documents_package_version(self):
        changelog = (Path(__file__).resolve().parents[1] / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## {__version__} —", changelog)

    def test_expected_release_version(self):
        self.assertEqual(__version__, "0.3.0")


if __name__ == "__main__":
    unittest.main()
