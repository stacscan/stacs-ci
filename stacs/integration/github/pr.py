"""STACS Github pull request integration.

SPDX-License-Identifier: BSD-3-Clause
"""

import json
import logging
import os
import sys
from json.decoder import JSONDecodeError
from typing import Dict, List

from stacs.integration import diff, exceptions, helpers
from stacs.integration.github.client import Client
from stacs.integration.github.constants import (
    FILE_COMMENT_TEMPLATE,
    NESTED_COMMENT_TEMPLATE,
)
from stacs.integration.models import SARIF


def validate_environment() -> List[str]:
    """Checks whether any required environment variables are missing."""
    missing = []
    required = [
        "GITHUB_TOKEN",
        "GITHUB_API_URL",
        "GITHUB_REPOSITORY",
        "GITHUB_SHA",
        "GITHUB_REF",
    ]

    for candidate in required:
        if os.environ.get(candidate) is None:
            missing.append(candidate)

    return missing


def position_in_diff(
    filepath: str,
    line: int,
    changes: Dict[str, Dict[int, diff.Hunk]],
) -> int:
    """Determine the position that the comment needs to be added in the diff."""
    position = 0

    # Check that the finding is present in a hunk which is part of this pull-request. A
    # finding may already be in a file modified in this pull-request, but not in one of
    # the locations which was modified. In this case, once again, a regular comment
    # will be added as we cannot annotate part of the file which was not modified by
    # this pull-request.
    for start, change in changes[filepath].items():
        # Determine the last line number of this hunk by counting all additions and
        # existing lines, but ignoring removals.
        current = int(start)
        contents = change["content"].splitlines()
        offset = change["offset"]

        for index, candidate in enumerate(contents):
            if candidate.startswith(("+", " ")) and index < len(contents) - 1:
                current += 1

            # Track the line number relative to the first diff hunk of this file - which
            # is the required offset to add a comment via the Github API.
            if line == current:
                position = offset + (index + 1)

        # If we already have a matching location, return it.
        if position:
            return position

    raise exceptions.ChangeNotInDiffException()


def main(sarif_file: str, prefix: str = None):
    """STACS Github pull request integration."""
    log = logging.getLogger(__name__)

    # Ensure the environment is as we expect (running in Github actions).
    missing_context = validate_environment()
    if missing_context:
        log.fatal(
            "Required environment variables are missing cannot continue: "
            f"{','.join(missing_context)}"
        )
        sys.exit(1)

    # Read in the input SARIF file.
    try:
        with open(os.path.abspath(os.path.expanduser(sarif_file)), "r") as fin:
            sarif = SARIF(json.load(fin))
    except (OSError, JSONDecodeError) as err:
        log.fatal(err)
        sys.exit(2)

    # Setup a Github API client.
    github = Client(api=os.environ["GITHUB_API_URL"], token=os.environ["GITHUB_TOKEN"])

    # Fetch and parse the pull-request diff from Github.
    try:
        changes = diff.parse(
            github.get_pull_request_diff(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
            )
        )
    except exceptions.ExternalServiceException as err:
        log.fatal(err)
        sys.exit(3)

    # Request a list of comments and issue comments from Github.
    comments = []
    try:
        comments.extend(
            github.get_issue_comments(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
            )
        )
        comments.extend(
            github.get_pull_request_review_comments(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
            )
        )
    except exceptions.ExternalServiceException as err:
        log.fatal(err)
        sys.exit(3)

    # Parse finding hashes (fhahes) from existing review and issue comments.
    fhashes = helpers.parse_fhashes(comments)

    # Roll over the findings and add a comment if they are not suppressed.
    for run in sarif.runs:
        rules = run.tool.rules
        artifacts = run.artifacts

        for finding in run.findings:
            if finding.suppressed:
                continue

            # Construct a virtual path for handling findings in nested files (archives),
            # and get the parent identifier.
            virtual_path = helpers.generate_virtual_path(finding, artifacts)

            try:
                parent = artifacts[finding.artifact].parent
            except exceptions.NoParentException:
                parent = None

            # Get a rule object using the finding rule id.
            rule = None
            for candidate in rules:
                if finding.rule == candidate.id:
                    rule = candidate

            # Determine if this finding already has a comment using the finding hash.
            fhash = helpers.generate_fhash(virtual_path, finding.offset, finding.rule)
            if fhash in fhashes:
                log.info(f"Found existing comment for finding ({fhash}), skipping.")
                continue

            # Only calculate the position in the diff if the file is both text, and is
            # directly in the repository (not inside an archive). We can check if the
            # finding has a line number to quickly check if the finding is inside a
            # binary.
            if finding.line and parent is None:
                position = position_in_diff(finding.filepath, finding.line, changes)

                github.add_pull_request_review_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment=FILE_COMMENT_TEMPLATE.format(
                        location=finding.location,
                        sample=finding.sample,
                        filename=finding.filepath,
                        rule=rule.id,
                        description=rule.description,
                        fhash=fhash,
                        version=run.tool.version,
                        suppression=helpers.generate_suppression(finding.filepath),
                    ),
                    filepath=finding.filepath,
                    position=position,
                    commit=os.environ["GITHUB_SHA"],
                )
                continue

            # Check if the finding is inside of an archive, and if so, generate a file
            # tree for easier location.
            if parent:
                github.add_issue_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment=NESTED_COMMENT_TEMPLATE.format(
                        location=finding.location,
                        sample=finding.sample,
                        filename=finding.filepath,
                        tree=helpers.get_file_tree(virtual_path=virtual_path),
                        rule=rule.id,
                        description=rule.description,
                        fhash=fhash,
                        version=run.tool.version,
                        suppression=helpers.generate_suppression(finding.filepath),
                    ),
                )
                continue

            # Otherwise, the finding is likely in a binary directly in the repository.
            github.add_issue_comment(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
                comment=FILE_COMMENT_TEMPLATE.format(
                    location=finding.location,
                    sample=finding.sample,
                    filename=finding.filepath,
                    rule=rule.id,
                    description=rule.description,
                    fhash=fhash,
                    version=run.tool.version,
                    suppression=helpers.generate_suppression(finding.filepath),
                ),
            )
