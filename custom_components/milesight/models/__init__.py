"""Per-model definitions (sensors, etc.)."""

from .wt101 import WT101_SENSORS, WT101_BINARIES

# Map model id -> sensor descriptions
MODEL_SENSORS = {
    "WT101": WT101_SENSORS,
}

# Map model id -> binary sensor descriptions
MODEL_BINARIES = {
    "WT101": WT101_BINARIES,
}
