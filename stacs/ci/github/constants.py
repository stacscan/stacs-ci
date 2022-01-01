"""STACS Github integration constants.

SPDX-License-Identifier: BSD-3-Clause
"""

DEFAULT_API_URI = "https://api.github.com"

# Finding is inside of a regular file.
FILE_COMMENT_TEMPLATE = (
    "### :x: [STACS](https://github.com/stacscan/stacs) Finding\n"
    "STACS has found a potential static token or credential at {location} of "
    "`{filename}` due to _{description}_.\n\n"
    "<details><summary>Finding Sample</summary>\n\n"
    "```\n"
    "...{sample}...\n"
    "```\n\n"
    "</details>\n\n"
    "If this credential is valid it should be immediately revoked, and the cause of "
    "this credential making it into this file investigated.\n\n"
    "If this finding is against a 'fake' credential, such as in a test fixture, this "
    "finding can be suppressed using an ignore list in the root of this repository. A "
    "basic ignore list entry can be found below which may be suitable, otherwise, "
    "please refer to the [STACS documentation](https://docs.stacs.app)\n\n"
    "<details><summary>Example Suppression</summary>\n\n"
    "```json\n{suppression}\n```\n\n"
    "</details>\n\n"
    "<sub>[**V**:{version}, **R**:{rule}, **F**:{fhash}]</sub>"
)

# Finding is nested inside of an archive.
NESTED_COMMENT_TEMPLATE = (
    "### :x: [STACS](https://github.com/stacscan/stacs) Finding\n"
    "STACS has found a potential static token or credential at {location} of "
    "`{filename}` due to _{description}_. Please be aware that this file is inside of "
    "an archive, the full path to the file is:\n\n"
    "```\n{tree}\n```\n\n"
    "<details><summary>Finding Sample</summary>\n\n"
    "```\n"
    "...{sample}...\n"
    "```\n\n"
    "</details>\n\n"
    "If this credential is valid it should be immediately revoked, and the cause of "
    "this credential making it into this file investigated.\n\n"
    "If this finding is against a 'fake' credential, such as in a test fixture, this "
    "finding can be suppressed using an ignore list in the root of this repository. A "
    "basic ignore list entry can be found below which may be suitable, otherwise, "
    "please refer to the [STACS documentation](https://docs.stacs.app)\n\n"
    "<details><summary>Example Suppression</summary>\n\n"
    "```json\n{suppression}\n```\n\n"
    "</details>\n\n"
    "<sub>[**V**:{version}, **R**:{rule}, **F**:{fhash}]</sub>"
)
