"""Switch entity helpers for Milesight."""

from __future__ import annotations

from .child_lock import MilesightChildLockSwitch
from .freeze_protection import MilesightFreezeProtectionSwitch

__all__ = ["MilesightChildLockSwitch", "MilesightFreezeProtectionSwitch"]
