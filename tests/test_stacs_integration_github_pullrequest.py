"""Tests the Github Pull Request integration."""

import json
import os
import unittest

from stacs.integration import exceptions
from stacs.integration.github import pull_request  # noqa: F401


class STACSIntegrationGithubPullRequest(unittest.TestCase):
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

    def test_get_position_in_diff(self):
        """Ensure that calculated offsets for test fixtures match expected values."""
        # Large dictionaries represnting findings and changes already parsed using their
        # respective functions are stashed as fixtures to prevent tests being difficult
        # to follow.
        changes = json.load(
            open(os.path.join(self.fixtures_path, "dicts/001.changes.json"), "r")
        )
        findings = json.load(
            open(os.path.join(self.fixtures_path, "dicts/001.findings.json"), "r")
        )
        artifacts = json.load(
            open(os.path.join(self.fixtures_path, "dicts/001.artifacts.json"), "r")
        )

        # Binary file offset won't exist in the diff, so an exception should be raised.
        with self.assertRaises(exceptions.ChangeNotInDiffException):
            pull_request.get_position_in_diff(
                finding=findings[0], changes=changes, artifacts=artifacts
            )

        # First finding in example_more should be at position 3.
        self.assertEqual(
            pull_request.get_position_in_diff(
                finding=findings[1], changes=changes, artifacts=artifacts
            ),
            3,
        )

        # Second finding in example_two should be at position 42.
        self.assertEqual(
            pull_request.get_position_in_diff(
                finding=findings[2], changes=changes, artifacts=artifacts
            ),
            42,
        )

        # The last finding has a filename which matches the second, but the file itself
        # is inside of an archive, so this should raise an exception.
        with self.assertRaises(exceptions.ChangeNotInDiffException):
            pull_request.get_position_in_diff(
                finding=findings[3], changes=changes, artifacts=artifacts
            )
