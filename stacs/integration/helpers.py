"""Helpers used by multiple STACS integrations.

SPDX-License-Identifier: BSD-3-Clause
"""

import hashlib
import json
import re
from typing import List

from stacs.integration.constants import PATH_SEPARATOR, PATTERN_FHASH
from stacs.integration.exceptions import NoParentException


def generate_virtual_path(finding: "Finding", artifacts: "List[Artifact]"):
    """Generate a virtual path for an input file."""
    virtual_path = finding.filepath

    try:
        parent = artifacts[finding.artifact].parent

        while True:
            name = artifacts[parent].filepath
            virtual_path = f"{name}{PATH_SEPARATOR}{virtual_path}"

            parent = artifacts[parent].parent
    except NoParentException:
        return virtual_path


def generate_fhash(filepath: str, offset: int, rule: str) -> str:
    """Generates a finding hash for use in de-duplicating comments."""
    return hashlib.sha1(bytes(f"{filepath}.{offset}.{rule}", "utf-8")).hexdigest()


def parse_fhashes(content: List[str]) -> List[str]:
    """Parses finding hashes from a list of text - such as Github comments."""
    fhashes = []

    for text in content:
        fhash = re.search(PATTERN_FHASH, text)
        if fhash:
            fhashes.append(fhash.group(1))

    return fhashes


def normalise_string(text: str) -> str:
    """Return the input string without the proceeding capital and trailing full-stop."""
    candidate = str()

    for index, char in enumerate(list(text)):
        if index == 0:
            candidate += char.lower()
        else:
            candidate += char

    return candidate.rstrip(".")


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


def get_file_tree(virtual_path: str) -> str:
    """Returns a tree layout to the virtual path."""
    tree = str()
    parts = virtual_path.split(PATH_SEPARATOR)

    for index, part in enumerate(parts):
        # Add some style. Print a package / box before each archive, and a document
        # before the file.
        if (index + 1) == len(parts):
            emoji = "📄"
        else:
            emoji = "📦"

        tree += f"{' ' * (index * 4)}`-- {emoji} {part}\n"

    return tree.rstrip()


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
