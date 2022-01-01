"""STACS Generic Integration.

This integration emits an exit status of non-zero if the provided SARIF file contains
any non-suppresssed findings.
"""

import json
import logging
import os
import sys
from json.decoder import JSONDecodeError

from colorama import Fore, init
from stacs.ci import constants, helpers
from stacs.ci.__about__ import __version__
from stacs.ci.models import SARIF


def main(sarif_file: str, prefix: str = None):
    log = logging.getLogger(__name__)

    # Colorama.
    init()

    # Read in the input SARIF file.
    try:
        with open(os.path.abspath(os.path.expanduser(sarif_file)), "r") as fin:
            sarif = SARIF(json.load(fin))
    except (OSError, JSONDecodeError) as err:
        log.fatal(err)
        sys.exit(1)

    # Find all unsuppressed findings, and track them separately.
    results = {}
    findings = 0

    for run in sarif.runs:
        tool = run.tool
        rules = run.tool.rules
        artifacts = run.artifacts

        for finding in run.findings:
            if finding.suppressed:
                continue

            # Get a rule object using the finding rule id.
            rule = None
            for candidate in rules:
                if finding.rule == candidate.id:
                    rule = candidate

            # Just one finding is enough to fail the build.
            findings += 1

            # Construct a virtual path for handling findings in nested files (archives),
            # and get the parent identifier.
            virtual_path = helpers.generate_virtual_path(finding, artifacts)
            if prefix:
                virtual_path = f"{prefix.rstrip('/')}/{virtual_path}"

            if results.get(virtual_path) is None:
                results[virtual_path] = []

            # Generates all strings for presentation now, rather than later.
            results[virtual_path].append(
                {
                    "tree": helpers.get_file_tree(virtual_path),
                    "path": finding.filepath,
                    "rule": finding.rule,
                    "text": rule.description,
                    "offset": finding.offset,
                    "line": finding.line,
                    "location": finding.location,
                    "sample": finding.sample,
                }
            )

    # Provide a summary.
    print(helpers.banner(tool_version=tool.version, version=__version__))

    if findings == 0:
        print("✨ " + Fore.GREEN + "No unsuppressed findings! Great work! ✨\n")
        sys.exit(0)

    # Render out the findings.
    print(
        f"{Fore.RED}🔥 There were {findings} unsuppressed findings in {len(results)} "
        "files 🔥\n"
    )

    for candidate in results:
        filepath = candidate.split(constants.PATH_SEPARATOR)[0]
        count = len(results[candidate])

        if constants.PATH_SEPARATOR in candidate:
            print(f"{Fore.RED}❌ {count} finding(s) inside of file {filepath} (Nested)")
        else:
            print(f"{Fore.RED}❌ {count} finding(s) inside of file {filepath}")

        for finding in results[candidate]:
            print()
            helpers.printi(f"{Fore.YELLOW}Reason   : {finding['text']}")
            helpers.printi(f"{Fore.YELLOW}Rule Id  : {finding['rule']}")
            helpers.printi(f"{Fore.YELLOW}Location : {finding['location']}\n\n")
            helpers.printi(f"{Fore.YELLOW}Filetree:\n\n")
            helpers.printi(
                finding["tree"],
                prefix=f"    {Fore.RESET}|{Fore.BLUE}",
            )
            print()
            helpers.printi(f"{Fore.YELLOW}Sample:\n\n")
            helpers.printi(
                f"... {finding['sample']} ...",
                prefix=f"    {Fore.RESET}|{Fore.BLUE}",
            )
            print()

        print(f"\n{Fore.RESET}{'-' * 78}\n")

    sys.exit(constants.FINDING_EXIT_CODE)
