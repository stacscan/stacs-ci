"""Processes diff files with Github pull-request semantics.

SPDX-License-Identifier: BSD-3-Clause
"""

import re
from typing import Dict, TypedDict

from stacs.ci.constants import PATTERN_GIT_DIFF_HEADER, PATTERN_GIT_DIFF_HUNK


class Hunk(TypedDict):
    content: str
    offset: int


def parse(raw: str) -> Dict[str, Dict[str, Hunk]]:
    """
    Parse a unified diff into a nested dictionary, keyed by filename and then line
    number of the given hunk.
    """
    changes = {}
    pointer = 0
    diff = raw.splitlines()

    while pointer < len(diff):
        # Check if the line is a 'git diff' file header, and if so, prepare a new entry
        # as this indicates a new file in the diff.
        match = re.match(PATTERN_GIT_DIFF_HEADER, diff[pointer])
        if match:
            line = "0"
            hunks = 0
            filename = match.group(2)
            changes[filename] = {}

        # Check if the line is a hunk start.
        match = re.match(PATTERN_GIT_DIFF_HUNK, diff[pointer])

        if match:
            # Track the 'range start' of this hunk hunk in the destination file.
            line = match.group(2).split(",")[0]

            # If this is the first hunk of this specific file, then track the location
            # as Github review comments are indexed by their location relative to the
            # first hunk.
            if hunks == 0:
                offset = pointer

            hunks += 1

        # Extract the contents of this hunk and track as is. Zero being 'Falsy' works to
        # our advantage here, as line 0 only exists if the file is being removed, in
        # which case we want to skip this block anyway.
        if int(line):
            if not changes[filename].get(line):
                changes[filename][line] = {"content": ""}

                # Offsets are referring to the count of lines after the first hunk
                # header for a given file. This is required when working with Github's
                # API for adding pull-request comments.
                if hunks == 1:
                    changes[filename][line]["offset"] = 1
                else:
                    changes[filename][line]["offset"] = (pointer - offset) + 1

            # Track the differences for this hunk as a blob of text. It doesn't matter
            # whether the real diff contains CRLF (\r\n or just LF (\n) as we just need
            # a way to determine when the line ends.
            if diff[pointer].startswith(("+", "-", " ")):
                changes[filename][line]["content"] += f"{diff[pointer]}\n"

        pointer += 1

    return changes
