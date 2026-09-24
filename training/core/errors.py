"""Training configuration errors."""

from __future__ import annotations


class TrainingConfigError(Exception):
    """Raised when training configuration is invalid."""


class TrainingDependencyError(Exception):
    """Raised when optional training dependencies are missing."""


class TrainingRegistryError(Exception):
    """Raised when model registry operations fail."""
