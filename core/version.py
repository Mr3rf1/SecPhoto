"""
SecPhoto Core Version Specification & Single Source of Truth
Conforms to Semantic Versioning 2.0.0 (https://semver.org/)
Decoupled from GUI/Presentation libraries (Constitution Principle IV)
"""

import re
import sys
from typing import Tuple, Optional, NamedTuple

# Canonical Application Identifiers & Version Constants
__version__ = "1.0.0"
VERSION_TUPLE: Tuple[int, int, int] = (1, 0, 0)
APP_NAME: str = "SecPhoto"
APP_SUBTITLE: str = "Telegram Self-Destructive Media Interceptor"

# Official SemVer 2.0.0 Regex Pattern
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


class VersionInfo(NamedTuple):
    """Structured representation of Semantic Version components."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @property
    def version_string(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s

    @property
    def version_tuple(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    @property
    def version_tag(self) -> str:
        return f"v{self.version_string}"


def parse_version(version_str: str) -> VersionInfo:
    """
    Parse an arbitrary SemVer 2.0.0 string into a structured VersionInfo.
    Raises ValueError if version_str does not strictly conform.
    """
    match = SEMVER_REGEX.match(version_str.strip())
    if not match:
        raise ValueError(f"Invalid Semantic Version 2.0.0 string: '{version_str}'")

    data = match.groupdict()
    return VersionInfo(
        major=int(data["major"]),
        minor=int(data["minor"]),
        patch=int(data["patch"]),
        prerelease=data.get("prerelease"),
        build=data.get("buildmetadata"),
    )


def get_version_string() -> str:
    """Return canonical version string (e.g., '1.0.0')."""
    return __version__


def get_version_tag() -> str:
    """Return version tag prefixed with 'v' (e.g., 'v1.0.0')."""
    return f"v{__version__}"


def get_window_title(subtitle: Optional[str] = None) -> str:
    """
    Generate the standardized desktop window title.
    Format: 'SecPhoto v{version} - {subtitle}'
    """
    sub = subtitle if subtitle is not None else APP_SUBTITLE
    return f"{APP_NAME} v{__version__} - {sub}"


def get_app_user_model_id(org: str = "Mr3rf1", component: str = "Interceptor") -> str:
    """
    Generate Windows AppUserModelID using major and minor version numbers.
    Format: '{org}.{APP_NAME}.{component}.{major}.{minor}'
    Example: 'Mr3rf1.SecPhoto.Interceptor.1.0'
    """
    parsed = parse_version(__version__)
    return f"{org}.{APP_NAME}.{component}.{parsed.major}.{parsed.minor}"
