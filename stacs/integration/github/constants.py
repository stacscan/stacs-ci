"""STACS Github integration constants.

SPDX-License-Identifier: BSD-3-Clause
"""

DEFAULT_API_URI = "https://api.github.com"

# Used to extract hashes of existing comments for deduplication.
PATTERN_FHASH = r"\*\*FHASH\*\*:([a-f0-9]{40})\]"

# Review comments are in-line comments on changes which are in pull-requests.
REVIEW_COMMENT_TEMPLATE = (
    "#### :x: STACS Finding\n"
    "STACS has found a potential static token or credential at line {line} of "
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
    "please refer to the [documentation on ignore lists](https://...)\n\n"
    "<details><summary>Example Suppression</summary>\n\n"
    "```json\n{suppression}\n```\n\n"
    "</details>\n\n"
    "<sub>Powered by [STACS](https://github.com/stacscan/stacs) (v{version})</sub> "
    "<sub>[**RULE**:{rule}, **FHASH**:{hash}]</sub>"
)

# There are two conditions where a comment needs to be added to the pull-request
# directly: Either the finding is inside a binary file, or the finding is in a file, or
# section of a file, which was not changed in this pull request.
COMMENT_TEMPLATE = """
    "#### :x: STACS Finding\n"
    "STACS has found a potential static token or credential at offset {offset}-bytes "
    "of `{filename}` due to _{description}_.\n\n"
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
    "please refer to the [documentation on ignore lists](https://...)\n\n"
    "<details><summary>Example Suppression</summary>\n\n"
    "```json\n{suppression}\n```\n\n"
    "</details>\n\n"
    "<sub>Powered by [STACS](https://github.com/stacscan/stacs) (v{version})</sub> "
    "<sub>[**RULE**:{rule}, **FHASH**:{hash}]</sub>"
"""
