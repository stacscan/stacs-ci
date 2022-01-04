"""STACS Github pull request integration.

SPDX-License-Identifier: BSD-3-Clause
"""

import json
import logging
import os
import sys
from json.decoder import JSONDecodeError
from typing import Dict, List

from stacs.ci import diff, exceptions, helpers
from stacs.ci.constants import FINDING_EXIT_CODE
from stacs.ci.github.client import Client
from stacs.ci.github.constants import FILE_COMMENT_TEMPLATE, NESTED_COMMENT_TEMPLATE
from stacs.ci.models import SARIF


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
    if filepath not in changes:
        raise exceptions.ChangeNotInDiffException()

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
            f"{', '.join(missing_context)}"
        )
        sys.exit(1)

    # Read in the input SARIF file.
    try:
        with open(os.path.abspath(os.path.expanduser(sarif_file)), "r") as fin:
            sarif = SARIF(json.load(fin))
    except (OSError, JSONDecodeError) as err:
        log.fatal(err)
        sys.exit(1)

    # Setup a Github API client.
    github = Client(api=os.environ["GITHUB_API_URL"], token=os.environ["GITHUB_TOKEN"])

    # Fetch and parse the pull-request diff from Github.
    log.info("Attempting to fetch and parse pull-request diff")
    try:
        changes = diff.parse(
            github.get_pull_request_diff(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
            )
        )
    except exceptions.ExternalServiceException as err:
        log.fatal(err)
        sys.exit(1)

    # Request a list of comments and issue comments from Github.
    comments = []
    try:
        log.info("Attempting to get existing pull-request comments")
        comments.extend(
            github.get_issue_comments(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
            )
        )

        log.info("Attempting to get existing pull-request review comments")
        comments.extend(
            github.get_pull_request_review_comments(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
            )
        )
    except exceptions.ExternalServiceException as err:
        log.fatal(err)
        sys.exit(1)

    # Parse finding hashes (fhahes) from existing review and issue comments.
    fhashes = helpers.parse_fhashes(comments)

    # Track unsupressed findings so that we can exit appropriately.
    unsuppressed = 0

    # Roll over the findings and add comments where required.
    for run in sarif.runs:
        rules = run.tool.rules
        artifacts = run.artifacts

        for finding in run.findings:
            # Construct a virtual path for handling findings in nested files (archives),
            # and get the parent identifier.
            filepath = finding.filepath
            virtual_path = helpers.generate_virtual_path(finding, artifacts)

            if prefix:
                filepath = f"{prefix.rstrip('/')}/{filepath}"
                virtual_path = f"{prefix.rstrip('/')}/{virtual_path}"

            # Skip the finding if it's suppressed, otherwise track it.
            if finding.suppressed:
                log.info(f"Skipping suppressed {finding.rule} finding in {filepath}")
                continue
            else:
                unsuppressed += 1

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
                log.info(
                    f"Found existing comment for {finding.rule} finding in {filepath}, "
                    f"skipping (FHASH:{fhash})"
                )
                continue

            # Only calculate the position in the diff if the file is both text, and is
            # directly in the repository (not inside an archive). We can check if the
            # finding has a line number to quickly check if the finding is inside a
            # binary.
            if finding.line and parent is None:
                # Only add a review comment if the file is present in the review.
                try:
                    position = position_in_diff(filepath, finding.line, changes)

                    log.info(
                        f"Attempting to add review comment for {finding.rule} finding "
                        f"in regular file at {filepath}"
                    )
                    github.add_pull_request_review_comment(
                        repository=os.environ["GITHUB_REPOSITORY"],
                        reference=os.environ["GITHUB_REF"],
                        comment=FILE_COMMENT_TEMPLATE.format(
                            location=finding.location,
                            sample=finding.sample,
                            filename=filepath,
                            rule=rule.id,
                            description=rule.description,
                            fhash=fhash,
                            version=run.tool.version,
                            suppression=helpers.generate_suppression(filepath),
                        ),
                        filepath=filepath,
                        position=position,
                        commit=os.environ["GITHUB_SHA"],
                    )
                    continue
                except exceptions.ChangeNotInDiffException:
                    # This case will be handled later.
                    pass

            # Check if the finding is inside of an archive, and if so, generate a file
            # tree for easier location.
            if parent:
                log.info(
                    f"Attempting to add pull-request comment for {finding.rule} "
                    f"finding in nested file at {filepath}"
                )
                github.add_issue_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment=NESTED_COMMENT_TEMPLATE.format(
                        location=finding.location,
                        sample=finding.sample,
                        filename=filepath,
                        tree=helpers.get_file_tree(virtual_path=virtual_path),
                        rule=rule.id,
                        description=rule.description,
                        fhash=fhash,
                        version=run.tool.version,
                        suppression=helpers.generate_suppression(filepath),
                    ),
                )
                continue

            # Otherwise, the finding is likely in a binary directly in the repository,
            # or a text file already in the target branch.
            log.info(
                f"Attempting to add pull-request comment for {finding.rule} "
                f"finding in file at {filepath}"
            )
            github.add_issue_comment(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
                comment=FILE_COMMENT_TEMPLATE.format(
                    location=finding.location,
                    sample=finding.sample,
                    filename=filepath,
                    rule=rule.id,
                    description=rule.description,
                    fhash=fhash,
                    version=run.tool.version,
                    suppression=helpers.generate_suppression(filepath),
                ),
            )

    if unsuppressed > 0:
        sys.exit(FINDING_EXIT_CODE)
    else:
        sys.exit(0)
