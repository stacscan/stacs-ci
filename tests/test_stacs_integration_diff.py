"""Tests the diff module."""

import os
import unittest

from stacs.integration import diff


class STACSIntegrationDiff(unittest.TestCase):
    """Tests the Github Pull Request integration."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        self.fixtures_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures/",
        )

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_parse(self):
        """Ensures that diff parsing is operating as expected."""
        # Ensure that a well formed diff can be parsed.
        valid = open(os.path.join(self.fixtures_path, "diff/001.txt"), "r").read()
        changes = diff.parse(valid)

        # Validate that all file names are properly extracted from the diff.
        expected = [
            "bcrypt",
            "example.txt",
            "example_more.txt",
            "example_two.txt",
            "moved",
            "remove",
        ]
        self.assertListEqual(expected, list(changes.keys()))

        # Validate that the file with two hunks ('example_two.txt') have the correct
        # offsets calculated.
        #
        # The first hunk starting at line 1 of the file should have an offset of 1.
        # The second hunk starting at line 56 of the file should have an offset of 38.
        #
        self.assertEqual(changes["example_two.txt"]["1"]["offset"], 1)
        self.assertEqual(changes["example_two.txt"]["56"]["offset"], 38)

        # Ensure that moved and removed files do not have any changes or offsets.
        self.assertEqual(changes["moved"], {})
        self.assertEqual(changes["remove"], {})
