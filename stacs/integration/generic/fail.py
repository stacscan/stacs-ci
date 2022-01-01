"""STACS Generic Integration.

This integration emits an exit status of non-zero if the provided SARIF file contains
any non-suppresssed findings.
"""

import json
import logging
import os
import sys
from json.decoder import JSONDecodeError

from stacs.integration.models import SARIF


def main(sarif_file: str, uri_base_id: str = None):
    log = logging.getLogger(__name__)

    # Read in the input SARIF file.
    try:
        with open(os.path.abspath(os.path.expanduser(sarif_file)), "r") as fin:
            sarif = SARIF(json.load(fin))
    except (OSError, JSONDecodeError) as err:
        log.fatal(err)
        sys.exit(1)

    # Find all unsuppressed findings, and track them separately.
    have_unsuppressed = False

    for run in sarif.runs:
        rules = run.tool.rules
        artifacts = run.artifacts

        for finding in run.findings:
            if finding.suppressed:
                continue

            # Just one finding is enough to fail the build.
            have_unsuppressed = True
