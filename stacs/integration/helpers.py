"""Helpers used by multiple STACS integrations.

SPDX-License-Identifier: BSD-3-Clause
"""

import hashlib
import json
import re
from typing import Any, Dict, List

import jmespath
from stacs.integration.constants import PATH_SEPARATOR


def string_difference(first: str, second: str):
    """Returns the portion of the first string which is not present in the second."""
    difference = str()

    for index, char in enumerate(list(first)):
        try:
            if char == second[index]:
                continue
            else:
                difference += char
        except IndexError:
            difference += char

    return difference


def get_virtual_path(artifact: int, artifacts: List[Dict[str, Any]]) -> str:
    """Returns the path to a file, including any 'virtual' component for archives."""
    full_path = jmespath.search("location.uri", artifacts[artifact])
    parent_id = artifacts[artifact].get("parentIndex")

    if parent_id:
        parent_path = get_virtual_path(artifact=parent_id, artifacts=artifacts)
        full_path = f"{parent_path}{PATH_SEPARATOR}{full_path}"

    return full_path


def get_file_tree(filename: str) -> str:
    """Returns a tree layout to the virtual filename."""
    tree = str()
    parts = filename.split(PATH_SEPARATOR)

    for index, part in enumerate(parts):
        if index == 0:
            tree += f"{part}\n"
        else:
            tree += f"{' ' * (index * 2)}└── {part}\n"

    return tree.rstrip()


def get_rule_id(finding: Dict[str, Any]) -> str:
    """Returns the rule identifier for a given finding."""
    return jmespath.search("ruleId", finding)


def get_original_base_uri(run: Dict[str, Any]) -> str:
    """Returns the original base URI (SRCROOT) for a given run."""
    return jmespath.search("originalUriBaseIds.SRCROOT.uri", run)


def get_filename(finding: Dict[str, Any]) -> str:
    """Returns the filename for a given finding."""
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


def generate_suppression(filepath: str):
    """Generate an example suppression document for the given file."""
    return json.dumps(
        {
            "include": [],
            "ignore": [
                {
                    "pattern": f"{re.escape(filepath)}$",
                    "reason": "A reason for this suppression",
                }
            ],
        },
        indent=4,
        sort_keys=True,
    )
