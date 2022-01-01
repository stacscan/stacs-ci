"""STACS CI Exceptions.

SPDX-License-Identifier: BSD-3-Clause
"""


class STACSIntegrationException(Exception):
    """The most generic form of exception raised by STACS integrations."""


class InvalidFindingException(STACSIntegrationException):
    """Indicates that a finding appears to be malformed."""


class NoParentException(STACSIntegrationException):
    """Indicates that a finding does not have a parent."""


class ChangeNotInDiffException(STACSIntegrationException):
    """Indicates that a finding does not appear in the current diff."""


class ExternalServiceException(STACSIntegrationException):
    """Indicates that an issue occurred while communicating with an external service."""
