"""Provides a light-weight Github API client that does only what we need.

SPDX-License-Identifier: BSD-3-Clause
"""

from typing import Dict

import requests
from stacs.integration import exceptions


class Client:
    """Provides a light-weight Github API client that does only what we need."""

    def __init__(self, api: str = "https://api.github.com", token: str = None):
        self.api = api.rstrip("/")
        self.token = token

    def _get(self, endpoint: str, headers: Dict[str, str]) -> requests.Response:
        """Wraps an HTTP GET to bolt on required headers."""

        # An authentication token isn't strictly required, so only add if present.
        request_headers = headers
        if self.token:
            request_headers["Authorization"] = f"token {self.token}"

        # Leave it to the caller to validate the response.
        return requests.get(f"{self.api}/{endpoint}", headers=request_headers)

    def _post(
        self,
        endpoint: str,
        headers: Dict[str, str],
        json: str = None,
    ) -> requests.Response:
        """Wraps an HTTP POST to bolt on required headers."""

        # An authentication token isn't strictly required, so only add if present.
        request_headers = headers
        if self.token:
            request_headers["Authorization"] = f"token {self.token}"

        # Leave it to the caller to validate the response.
        return requests.post(
            f"{self.api}/{endpoint}",
            json=json,
            headers=request_headers,
        )

    def get_pull_request_diff(self, repository: str, reference: str) -> str:
        """Fetches and returns the pull-request diff from Github."""
        pull = reference.split("/")[-2]

        try:
            response = self._get(
                f"repos/{repository}/pulls/{pull}",
                headers={"Accept": "application/vnd.github.v3.diff"},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise exceptions.ExternalServiceException(
                f"An error occurred fetching the diff for this pull-request: {err}"
            )

        return response.text

    def add_pull_request_review_comment(
        self,
        repository: str,
        reference: str,
        comment: str,
        commit: str,
        filepath: str,
        position: int,
    ):
        """Adds the pull-request review comment to the provided line number."""
        pull = reference.split("/")[-2]

        try:
            response = self._post(
                f"repos/{repository}/pulls/{pull}/comments",
                headers={"Accept": "application/vnd.github.v3+json"},
                json={
                    "body": comment,
                    "commit_id": commit,
                    "path": filepath,
                    "position": position,
                },
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise exceptions.ExternalServiceException(
                f"An error occurred adding a review comment to this pull-request: {err}"
            )

    def add_issue_comment(self, repository: str, reference: str, comment: str):
        """Adds a comment to a Github issue."""
        pull = reference.split("/")[-2]

        try:
            response = self._post(
                f"repos/{repository}/issues/{pull}/comments",
                headers={"Accept": "application/vnd.github.v3+json"},
                json={"body": comment},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise exceptions.ExternalServiceException(
                f"An error occurred adding a comment to this pull-request: {err}"
            )
