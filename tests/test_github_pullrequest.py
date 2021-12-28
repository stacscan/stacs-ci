"""Tests the Github Pull Request integration."""

import unittest

import stacs.integration  # noqa: F401


class IntegrationGithubPullRequest(unittest.TestCase):
    """Tests the Github Pull Request integration."""

    def setUp(self):
        """Ensure the application is setup for testing."""
        pass

    def tearDown(self):
        """Ensure everything is torn down between tests."""
        pass

    def test_noop(self):
        """Does nothing, successfully to keep tox happy."""
        return True
