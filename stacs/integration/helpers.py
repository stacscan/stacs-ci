"""Helpers used by multiple STACS integrations.

SPDX-License-Identifier: BSD-3-Clause
"""

import json
import re

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


def get_file_tree(filename: str) -> str:
    """Returns a tree layout to the virtual filename."""
    tree = str()
    parts = filename.split(PATH_SEPARATOR)

    for index, part in enumerate(parts):
        # Add some style. Print a package / box before each archive, and a document
        # before the file.
        if (index + 1) == len(parts):
            emoji = "📄"
        else:
            emoji = "📦"

        if index == 0:
            tree += f"{emoji} {part}\n"
        else:
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
