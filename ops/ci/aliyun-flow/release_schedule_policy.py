#!/usr/bin/env python3
"""Pure release-window classification for the CYF Flow control plane.

It deliberately never starts a Flow run, mutates a pipeline, or rejects a
release. Callers use its result to select a window and record unknown inputs.
Compatible with the host's Python 3.6 runtime.
"""

import re

_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def parse_stable_version(value):
    """Return a (major, minor, patch) tuple, otherwise None (never a gate)."""
    if not isinstance(value, str):
        return None
    match = _VERSION.fullmatch(value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def frontend_release_lane(installed, candidate):
    """Classify without blocking: immediate, scheduled-major, or unclassified."""
    current = parse_stable_version(installed)
    next_version = parse_stable_version(candidate)
    if current is None or next_version is None:
        return "unclassified"
    if next_version[0] > current[0]:
        return "scheduled-major"
    if next_version[0] == current[0] and next_version[1] - current[1] >= 2:
        return "scheduled-major"
    return "immediate"


def backend_release_lane(hour_beijing):
    """Return build-only during [06:00, 24:00), otherwise the release window."""
    if not isinstance(hour_beijing, int) or not 0 <= hour_beijing <= 23:
        raise ValueError("hour_beijing must be an integer from 0 through 23")
    return "build-only" if 6 <= hour_beijing < 24 else "release-window"
