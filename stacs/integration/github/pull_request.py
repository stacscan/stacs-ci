"""STACS Github pull request integration.

SPDX-License-Identifier: BSD-3-Clause
"""


import argparse
import json
import logging
import os
import re
import sys
from json.decoder import JSONDecodeError
from typing import Any, Dict, List

from stacs.integration import diff, exceptions, helpers
from stacs.integration.github.client import Client
from stacs.integration.github.constants import (
    FILE_COMMENT_TEMPLATE,
    NESTED_COMMENT_TEMPLATE,
    PATTERN_FHASH,
)


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


def get_position_in_diff(
    finding: Dict[str, Any],
    changes: Dict[str, Dict[int, diff.Hunk]],
    artifacts: Dict[str, Any],
) -> int:
    """Determine the position that the comment needs to be added in the diff."""
    filename = helpers.get_filename(finding)
    artifact = helpers.get_artifact_index(finding)
    comment_location = 0

    # If there is no line-number, the finding is very likely inside of a binary. Github
    # does not allow review comments on binaries, so we'll need to just add a regular
    # review comment.
    #
    # This should also take care of nested files, as all archive formats will be binary,
    # which prevents the need for an additional check here.
    line = helpers.get_start_line(finding)
    if not line:
        raise exceptions.ChangeNotInDiffException()

    # Check whether this finding has a parent, which would indicate that it is from a
    # file inside of an archive - so it won't be present in the diff directly.
    if helpers.has_parent(artifact, artifacts):
        raise exceptions.ChangeNotInDiffException()

    # Check that the finding is inside a file present in the diff. A finding may be in
    # a file which was not modified as part ofthis pull-request, in which case a regular
    # comment will be added once again, as Github won't let us annotate a file outside
    # of this pull request.
    if filename not in changes:
        raise exceptions.ChangeNotInDiffException()

    # Check that the finding is present in a hunk which is part of this pull-request. A
    # finding may already be in a file modified in this pull-request, but not in one of
    # the locations which was modified. In this case, once again, a regular comment
    # will be added as we cannot annotate part of the file which was not modified by
    # this pull-request.
    for start, change in changes[filename].items():
        # Determine the last line number of this hunk by counting all additions and
        # existing lines, but ignoring removals.
        position = int(start)
        contents = change["content"].splitlines()
        offset = change["offset"]

        for index, candidate in enumerate(contents):
            if candidate.startswith(("+", " ")) and index < len(contents) - 1:
                position += 1

            # Track the line number relative to the first diff hunk of this file - which
            # is the required offset to add a comment via the Github API.
            if line == position:
                comment_location = offset + (index + 1)

        # If we already have a matching location, break out of the loop early.
        if comment_location:
            break

    # If we don't have a location, it's likely that the change was already inside of the
    # file, so we'll just add a regular pull-request comment.
    if not comment_location:
        raise exceptions.ChangeNotInDiffException()

    return comment_location


def main():
    """STACS Github pull request integration."""
    parser = argparse.ArgumentParser(
        description="Annotates Github pull requests with STACS unsuppressed findings."
    )
    parser.add_argument("sarif", help="Path to the SARIF file to process")
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(process)d - [%(levelname)s] %(message)s",
    )
    log = logging.getLogger(__name__)

    # Ensure the environment is as we expect (running in Github actions).
    missing_env = validate_environment()

    if missing_env:
        log.fatal(
            "Required environment variables are missing cannot continue: "
            f"{','.join(missing_env)}"
        )
        sys.exit(2)

    # Read in the input SARIF file.
    try:
        with open(os.path.abspath(os.path.expanduser(arguments.sarif)), "r") as fin:
            sarif = json.load(fin)
    except (OSError, JSONDecodeError) as err:
        log.fatal(err)
        sys.exit(3)

    # Perform a cheap check whether the trigger was a pull request.
    if "/pull/" not in os.environ["GITHUB_REF"]:
        log.info("Trigger does not appear to be a pull request, exiting.")
        sys.exit(0)

    # Setup a Github API client.
    github = Client(
        api=os.environ["GITHUB_API_URL"],
        token=os.environ["GITHUB_TOKEN"],
    )

    # Fetch and parse the diff from Github.
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

    # Parse finding hashes from review comments.
    existing_findings = []

    for comment in comments:
        fhash = re.search(PATTERN_FHASH, comment)
        if fhash:
            existing_findings.append(fhash.group(1))

    # Roll over the findings and add a comment if they are not suppressed.
    for run in sarif.get("runs", []):
        tool = run.get("tool", [])
        artifacts = run.get("artifacts", [])
        version = helpers.get_stacs_version(tool=tool)

        # TODO: We should deserialise the results ('findings') into a model, and use
        # properties to access all of the required attributes, rather than needing lots
        # of get_* helpers.
        for result in run.get("results"):
            if helpers.finding_suppressed(result):
                continue

            # Extract data from the finding required for this comment.
            line = helpers.get_start_line(finding=result)
            hash = helpers.get_finding_hash(finding=result, artifacts=artifacts)
            rule = helpers.get_rule_id(finding=result)
            sample = helpers.get_sample(finding=result)
            offset = helpers.get_offset(finding=result)
            filename = helpers.get_filename(finding=result)
            suppression = helpers.get_suppression(filename=filename)
            description = helpers.get_rule_description(rule=rule, tool=tool)
            artifact_index = helpers.get_artifact_index(finding=result)
            virtual_path = helpers.get_virtual_path(
                artifact=artifact_index,
                artifacts=artifacts,
            )

            # Skip adding a comment if one already exists.
            if hash in existing_findings:
                log.info(
                    f"Skipping comment for finding, as hash for finding {hash} already "
                    "exists."
                )
                continue

            # Calculate the position in the diff to add the review comment, and add it.
            try:
                position = get_position_in_diff(
                    finding=result,
                    changes=changes,
                    artifacts=artifacts,
                )

                github.add_pull_request_review_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment=FILE_COMMENT_TEMPLATE.format(
                        location=f"line `{line}`",
                        sample=sample,
                        filename=filename,
                        rule=rule,
                        description=description,
                        suppression=suppression,
                        hash=hash,
                        version=version,
                    ),
                    filepath=filename,
                    position=position,
                    commit=os.environ["GITHUB_SHA"],
                )

                continue
            except exceptions.ChangeNotInDiffException:
                # If the file changed wasn't in the diff, then we'll need to add a
                # regular comment.
                log.warning(
                    "Finding does not appear in the current diff, adding regular "
                    "comment to pull-request"
                )

            # Offsets for binaries are in bytes, where text is in lines.
            if line:
                location = f"line `{line}`"
            else:
                location = f"{offset}-bytes"

            # If the finding is inside of an archive, show the filename as a nested
            # path, rather than a single file name.
            if helpers.has_parent(artifact=artifact_index, artifacts=artifacts):
                github.add_issue_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment=NESTED_COMMENT_TEMPLATE.format(
                        location=location,
                        sample=sample,
                        filename=filename,
                        tree=helpers.get_file_tree(filename=virtual_path),
                        rule=rule,
                        description=description,
                        suppression=suppression,
                        hash=hash,
                        version=version,
                    ),
                )
                continue

            # Otherwise, the finding is likely directly in a binary which is in the
            # repository.
            github.add_issue_comment(
                repository=os.environ["GITHUB_REPOSITORY"],
                reference=os.environ["GITHUB_REF"],
                comment=FILE_COMMENT_TEMPLATE.format(
                    location=location,
                    sample=sample,
                    filename=filename,
                    rule=rule,
                    description=description,
                    suppression=suppression,
                    hash=hash,
                    version=version,
                ),
            )


if __name__ == "__main__":
    main()
