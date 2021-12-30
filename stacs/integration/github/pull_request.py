"""STACS Github pull request integration.

SPDX-License-Identifier: BSD-3-Clause
"""

import argparse
import json
import logging
import os
import sys
from json.decoder import JSONDecodeError
from typing import Any, Dict, List

import jmespath
from stacs.integration import diff, exceptions
from stacs.integration.github.client import Client


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


def finding_suppressed(finding: Dict[str, Any]) -> bool:
    """Checks whether a finding is suppressed."""
    suppressions = finding.get("suppressions", [])

    if not suppressions:
        return False

    # Findings may be listed as suppressed but with a status of 'rejected', 'accepted',
    # or 'underReview'. If the suppression isn't 'accepted' then we'll still annotate.
    for suppression in suppressions:
        if suppression.get("status", str()).lower() != "accepted":
            return False

    return True


def has_parent(artifact: int, artifacts: Dict[str, Any]) -> bool:
    """Checks whether the given artifact has a parent, indicating it is an archive."""
    if artifacts[artifact].get("parentIndex") is not None:
        return True

    return False


def get_finding_hash(finding: Dict[str, Any]) -> str:
    """Generates a hash for the finding for use in de-duplicating comments."""
    pass


def get_filename(finding: Dict[str, Any]) -> str:
    """Returns the filename for a given finding."""
    return jmespath.search(
        "locations[0].physicalLocation.artifactLocation.uri",
        finding,
    )


def get_position_in_diff(
    finding: Dict[str, Any],
    changes: Dict[str, Dict[int, diff.Hunk]],
    artifacts: Dict[str, Any],
) -> int:
    """Determine the position that the comment needs to be added in the diff."""
    location = finding.get("locations", [])
    if not location:
        raise exceptions.InvalidFindingException("No locations present in finding.")

    # STACS should only ever generate a single location per finding, so we don't need to
    # loop here.
    location = location[0]
    filename = jmespath.search("physicalLocation.artifactLocation.uri", location)
    artifact = jmespath.search("physicalLocation.artifactLocation.index", location)
    comment_location = 0

    # If there is no line-number, the finding is very likely inside of a binary. Github
    # does not allow review comments on binaries, so we'll need to just add a regular
    # review comment.
    #
    # This should also take care of nested files, as all archive formats will be binary,
    # which prevents the need for an additional check here.
    line = jmespath.search("physicalLocation.region.startLine", location)
    if not line:
        raise exceptions.ChangeNotInDiffException()

    # Check whether this finding has a parent, which would indicate that it is from a
    # file inside of an archive - so it won't be present in the diff directly.
    if has_parent(artifact, artifacts):
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

    # TODO: Get a list of all comments, and review comments here. Generating a list of
    # hashes which are already annotated.

    # Roll over the findings and add a comment if they are not suppressed.
    for run in sarif.get("runs", []):
        artifacts = run.get("artifacts", [])

        for result in run.get("results"):
            if finding_suppressed(result):
                continue

            # Calculate the line number we need to pass to Github in order to add a
            # comment to the correct location.
            review_comment = True

            try:
                line = get_position_in_diff(
                    finding=result,
                    changes=changes,
                    artifacts=artifacts,
                )
            except exceptions.ChangeNotInDiffException:
                review_comment = False
                log.warning(
                    "Finding does not appear in the current diff, adding regular "
                    "comment to pull-request"
                )
            except exceptions.InvalidFindingException as err:
                log.fatal(err)
                sys.exit(4)

            # If no line number was found, then the comment must be added as a regular
            # pull-request comment. This usually indicates that the finding is present
            # in a file not part of this pull-request, or part of the file which was
            # not changed.
            filename = get_filename(finding=result)

            # TODO: Check for finding hash in comment hashes.
            # ... get_finding_hash(finding)

            if review_comment:
                github.add_pull_request_review_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment="This is a test",
                    filepath=filename,
                    position=line,
                    commit=os.environ["GITHUB_SHA"],
                )
            else:
                github.add_issue_comment(
                    repository=os.environ["GITHUB_REPOSITORY"],
                    reference=os.environ["GITHUB_REF"],
                    comment=f"This is a binary / nested finding for {filename}",
                )


if __name__ == "__main__":
    main()
