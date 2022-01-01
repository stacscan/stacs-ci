"""Define constants commonly used throughout STACS CI.

SPDX-License-Identifier: BSD-3-Clause
"""

PATTERN_GIT_DIFF_HEADER = r"^diff\s+.*?a/(.*?)\s+b/(.*)$"
PATTERN_GIT_DIFF_HUNK = r"@@\s+-([0-9,]+)\s+\+([0-9,]+)\s+.*@@"

PATH_SEPARATOR = "!"

# Used to extract hashes of existing comments / bodies of text for deduplication.
PATTERN_FHASH = r"\s+\*\*F\*\*:([a-f0-9]{40})]"

# The exit code to use when there is an unsupressed finding.
FINDING_EXIT_CODE = 100
