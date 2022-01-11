"""Tests the Github Pull Request integration."""

import json
import os
import unittest

from stacs.ci import exceptions
from stacs.ci.github import pr
from stacs.ci.models import SARIF


class STACSCIGithubPullRequest(unittest.TestCase):
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

    def test_position_in_diff(self):
        """Ensure that calculated offsets for test fixtures match expected values."""
        # Large dictionaries represnting findings and changes already parsed using their
        # respective functions are stashed as fixtures to prevent tests being difficult
        # to follow.
        changes = json.load(
            open(os.path.join(self.fixtures_path, "dicts/001.changes.json"), "r")
        )

        # Load SARIF to get findings.
        sarif = SARIF(
            json.load(open(os.path.join(self.fixtures_path, "sarif/001.json"), "r"))
        )
        runs = sarif.runs
        findings = runs[0].findings

        # First finding in example_more should be at position 3 in the diff.
        self.assertEqual(
            pr.position_in_diff(findings[0].filepath, findings[0].line, changes), 3
        )

        # Binary file offset won't exist in the diff, so an exception should be raised.
        with self.assertRaises(exceptions.ChangeNotInDiffException):
            pr.position_in_diff(findings[1].filepath, findings[1].line, changes)

        # First finding in example_two should be at position 7 in the diff.
        self.assertEqual(
            pr.position_in_diff(findings[4].filepath, findings[4].line, changes), 7
        )

        # Second finding in example_two should be at position 42 in the diff.
        self.assertEqual(
            pr.position_in_diff(findings[5].filepath, findings[5].line, changes), 42
        )

        # Finding at the first line of a new file (cookies) should be at position 1 in
        # the diff.
        self.assertEqual(
            pr.position_in_diff(findings[6].filepath, findings[6].line, changes), 1
        )
