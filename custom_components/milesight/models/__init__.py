"""Per-model definitions (sensors, etc.)."""

from .wt101 import WT101_SENSORS

# Map model id -> sensor descriptions
MODEL_SENSORS = {
    "wt101": WT101_SENSORS,
}
