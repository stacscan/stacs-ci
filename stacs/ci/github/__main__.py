"""Provides a generic entrypoint for the STACS Github integration. """
import argparse
import logging

from stacs.ci.github import pr

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "STACS Github integration: Annotates Github pull requests with STACS "
            "findings."
        )
    )
    parser.add_argument(
        "sarif",
        help="Path to the SARIF file to process",
    )
    parser.add_argument(
        "--prefix",
        help=(
            "The path to a sub-directory under the repository root the scan was"
            "executed from"
        ),
    )
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(process)d - [%(levelname)s] %(message)s",
    )
    log = logging.getLogger(__name__)

    # So far we only support pull-requests, but that may change in future.
    pr.main(sarif_file=arguments.sarif, prefix=arguments.prefix)
