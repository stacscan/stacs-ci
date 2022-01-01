"""Provides a light-weight Github API client that does only what we need.

SPDX-License-Identifier: BSD-3-Clause
"""

from typing import Dict, List

import requests
from stacs.ci import exceptions
from stacs.ci.github.constants import DEFAULT_API_URI


class Client:
    """Provides a light-weight Github API client that does only what we need."""

    def __init__(self, api: str = DEFAULT_API_URI, token: str = None):
        self.api = api.rstrip("/")
        self.token = token

    def _get(
        self,
        endpoint: str,
        headers: Dict[str, str] = None,
        params: Dict[str, str] = None,
    ) -> requests.Response:
        """Wraps an HTTP GET to bolt on required headers."""

        # An authentication token isn't strictly required, so only add if present.
        request_headers = headers
        if self.token:
            request_headers["Authorization"] = f"token {self.token}"

        # Leave it to the caller to validate the response.
        return requests.get(
            f"{self.api}/{endpoint}",
            headers=request_headers,
            params=params,
        )

    def _post(
        self,
        endpoint: str,
        headers: Dict[str, str] = None,
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

    def get_pull_request_review_comments(
        self,
        repository: str,
        reference: str,
    ) -> List[str]:
        """Fetches and returns a list of pull-request review comments from Github."""
        pull = reference.split("/")[-2]
        page = 1
        per_page = 100

        # We only care about the body, so we'll just return a list of text.
        comments = []

        while True:
            try:
                response = self._get(
                    f"repos/{repository}/pulls/{pull}/comments",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    params={
                        "page": page,
                        "per_page": per_page,
                    },
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                raise exceptions.ExternalServiceException(
                    f"An error occurred fetching the diff for this pull-request: {err}"
                )

            # Track the comment.
            for comment in response.json():
                comments.append(comment.get("body"))

            # Check if there are more records to fetch.
            if len(response.json()) != per_page:
                break

        return comments

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

    def get_issue_comments(
        self,
        repository: str,
        reference: str,
    ) -> List[str]:
        """Fetches and returns a list of issue comments from Github."""
        pull = reference.split("/")[-2]
        page = 1
        per_page = 100

        # We only care about the body, so we'll just return a list of text.
        comments = []

        while True:
            try:
                response = self._get(
                    f"repos/{repository}/issues/{pull}/comments",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    params={
                        "page": page,
                        "per_page": per_page,
                    },
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                raise exceptions.ExternalServiceException(
                    f"An error occurred fetching the diff for this pull-request: {err}"
                )

            # Track the comment.
            for comment in response.json():
                comments.append(comment.get("body"))

            # Check if there are more records to fetch.
            if len(response.json()) != per_page:
                break

        return comments

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
