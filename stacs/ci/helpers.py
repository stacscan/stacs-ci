"""Helpers used by multiple STACS CI.

SPDX-License-Identifier: BSD-3-Clause
"""

import hashlib
import json
import re
from typing import List

import colorama
from stacs.ci.constants import PATH_SEPARATOR, PATTERN_FHASH
from stacs.ci.exceptions import NoParentException


def generate_virtual_path(
    finding: "Finding",  # noqa: F821
    artifacts: "List[Artifact]",  # noqa: F821
):
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


def generate_suppression(filepath: str) -> str:
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


def printi(string, indent: int = 4, prefix: str = None):
    """Super janky wrapper to print something indented."""
    for line in string.splitlines():
        if prefix:
            print(f"{prefix}", end="")

        print(f"{' ' * indent}" + line)


def banner(version: str, tool_version: str) -> str:
    """Returns a STACS console banner."""
    banner = colorama.Fore.BLUE
    banner += rf"""
    ______________   ___________
   / ___/_  __/   | / ____/ ___/
   \__ \ / / / /| |/ /    \__ \
  ___/ // / / ___ / /___ ___/ /
 /____//_/ /_/  |_\____//____/

       STACS version {tool_version}
 STACS Integration Version {version}
    """
    return banner
