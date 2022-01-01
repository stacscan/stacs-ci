"""Models used by STACS CI.

SPDX-License-Identifier: BSD-3-Clause
"""

from typing import Any, Dict, List

import jmespath
from stacs.ci.exceptions import NoParentException
from stacs.ci.helpers import normalise_string


class SARIFObject:
    def __init__(self, raw: Dict[str, Any]):
        self._raw = raw

    def by_path(self, path: str, default: Any = None) -> Any:
        """Returns a given field by JMESPath, or the default if not found."""
        candidate = jmespath.search(path, self._raw)

        if candidate is None:
            return default
        else:
            return candidate


class Finding(SARIFObject):
    @property
    def location(self) -> str:
        """Returns a plain-text location slug, preferring line numbers to offsets."""
        if self.line:
            return f"line {self.line}"
        else:
            return f"{self.offset}-bytes"

    @property
    def suppressed(self) -> bool:
        """Indicates whether this finding is suppressed."""
        # Determine if this finding is suppressed.
        candidates = self.by_path("suppressions", [])

        if not candidates:
            return False

        # A finding may be listed as suppressed but with a status that isn't 'accepted',
        # in which case the finding isn't actually suppressed.
        for suppression in candidates:
            if suppression.get("status", str()).lower() != "accepted":
                return False

        return True

    @property
    def rule(self):
        """Returns the rule identifier from the finding."""
        return self.by_path("ruleId")

    @property
    def filepath(self):
        """Returns the path to the file the finding was found in."""
        return self.by_path("locations[0].physicalLocation.artifactLocation.uri")

    @property
    def offset(self):
        """Returns the byte offset of the finding."""
        return int(self.by_path("locations[0].physicalLocation.region.byteOffset"))

    @property
    def artifact(self):
        """Returns the artifact index of the finding."""
        return int(self.by_path("locations[0].physicalLocation.artifactLocation.index"))

    @property
    def line(self):
        """Returns the line number which the finding starts at, if applicable."""
        line = self.by_path("locations[0].physicalLocation.region.startLine")

        if line:
            return int(line)
        else:
            return 0

    @property
    def sample(self):
        """Returns the sample from the finding."""
        # Prefer a 'text' sample, if present.
        candidate = self.by_path(
            "locations[0].physicalLocation.contextRegion.snippet.text"
        )
        if candidate:
            return candidate

        # Otherwise return a 'binary' sample.
        return self.by_path(
            "locations[0].physicalLocation.contextRegion.snippet.binary"
        )


class Rule(SARIFObject):
    @property
    def id(self) -> str:
        """Returns the rule identifier."""
        return self.by_path("id", "Unknown")

    @property
    def description(self) -> str:
        """Returns the rule description."""
        return normalise_string(self.by_path("shortDescription.text", "Unknown"))


class Tool(SARIFObject):
    @property
    def version(self) -> str:
        """Returns the tool version."""
        return self.by_path("driver.version", "Unknown")

    @property
    def rules(self) -> List[Rule]:
        """Return a list of Rule objects."""
        candidates = []

        for candidate in self.by_path("driver.rules", []):
            candidates.append(Rule(candidate))

        return candidates


class Artifact(SARIFObject):
    @property
    def filepath(self) -> str:
        """Returns the file path for the artifact"""
        return self.by_path("location.uri")

    @property
    def parent(self) -> int:
        """Gets the artifact index for the parent of this artifact."""
        candidate = self.by_path("parentIndex", None)

        if candidate is not None:
            return int(candidate)
        else:
            raise NoParentException()


class Run(SARIFObject):
    @property
    def findings(self) -> List[Finding]:
        """Returns a list of Finding objects."""
        candidates = []

        for candidate in self.by_path("results", []):
            candidates.append(Finding(candidate))

        return candidates

    @property
    def tool(self) -> str:
        """Returns a Tool object."""
        return Tool(self.by_path("tool"))

    @property
    def artifacts(self) -> List[Artifact]:
        """Returns a list of Artifact objects."""
        candidates = []

        for candidate in self.by_path("artifacts", []):
            candidates.append(Artifact(candidate))

        return candidates


class SARIF(SARIFObject):
    @property
    def version(self) -> str:
        """Returns the version of SARIF this document conforms to."""
        return self.by_path("version")

    @property
    def runs(self) -> List[Run]:
        """Retuns a list of Run objects."""
        candidates = []

        for candidate in self.by_path("runs", []):
            candidates.append(Run(candidate))

        return candidates
