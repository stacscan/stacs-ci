"""Helpers used by multiple STACS integrations.

SPDX-License-Identifier: BSD-3-Clause
"""

import hashlib
import json
import re
from typing import Any, Dict

import jmespath


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


def get_stacs_version(tool: Dict[str, Any]) -> str:
    """Returns the current STACS version from the tool section of the SARIF document."""
    version = jmespath.search("driver.version", tool)
    if not version:
        return "Unknown"

    return version


def get_rule_description(rule: str, tool: Dict[str, Any]) -> str:
    """Returns a normalised plain-text description for a given rule id."""
    rules = jmespath.search("driver.rules", tool)
    if not rules:
        return "unknown"

    for candidate in rules:
        if candidate.get("id") == rule:
            # Strip proceeding capital letter and trailing full-stop, if present.
            raw = jmespath.search("shortDescription.text", candidate)
            description = str()

            for index, char in enumerate(list(raw)):
                description += char
                if index == 0:
                    description = description.lower()

            return description.rstrip(".")

    return "unknown"


def get_finding_hash(finding: Dict[str, Any]) -> str:
    """Generates a hash for the finding for use in de-duplicating comments."""
    filename = get_filename(finding)
    offset = get_offset(finding)
    rule = get_rule_id(finding)

    return hashlib.sha1(bytes(f"{filename}.{offset}.{rule}", "utf-8")).hexdigest()


def get_rule_id(finding: Dict[str, Any]) -> str:
    """Returns the rule identifier for a given finding."""
    return jmespath.search("ruleId", finding)


def get_filename(finding: Dict[str, Any]) -> str:
    """Returns the filename for a given finding."""
    #
    # TODO: If nested...?
    #
    # if has_parent(get_artifact_index(finding), artifacts):
    return jmespath.search(
        "locations[0].physicalLocation.artifactLocation.uri",
        finding,
    )


def get_offset(finding: Dict[str, Any]) -> int:
    """Returns the byte offset of a given finding."""
    return int(
        jmespath.search(
            "locations[0].physicalLocation.region.byteOffset",
            finding,
        )
    )


def get_artifact_index(finding: Dict[str, Any]) -> int:
    """Returns the artifact index for a given finding."""
    return int(
        jmespath.search(
            "locations[0].physicalLocation.artifactLocation.index",
            finding,
        )
    )


def get_sample(finding: Dict[str, Any]) -> str:
    """Returns the sample for a given finding."""
    # Determine whether a text or binary sample should be returned - with preference to
    # text.
    text = jmespath.search(
        "locations[0].physicalLocation.contextRegion.snippet.text", finding
    )
    if text:
        return text

    return jmespath.search(
        "locations[0].physicalLocation.contextRegion.snippet.binary", finding
    )


def get_start_line(finding: Dict[str, Any]) -> int:
    """Returns the line number which a given finding starts at."""
    line = jmespath.search("locations[0].physicalLocation.region.startLine", finding)

    if line:
        return int(line)
    else:
        return 0


def get_suppression(filename: str):
    """Generate an example suppression document for the given file."""
    return json.dumps(
        {
            "include": [],
            "ignore": [
                {
                    "pattern": f"{re.escape(filename)}$",
                    "reason": "A reason for this suppression",
                }
            ],
        },
        indent=4,
        sort_keys=True,
    )