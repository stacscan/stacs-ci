"""Define constants commonly used throughout STACS Integrations.

SPDX-License-Identifier: BSD-3-Clause
"""

PATTERN_GIT_DIFF_HEADER = r"^diff\s+.*?a/(.*?)\s+b/(.*)$"
PATTERN_GIT_DIFF_HUNK = r"@@\s+-([0-9,]+)\s+\+([0-9,]+)\s+.*@@"

PATH_SEPARATOR = "!"
