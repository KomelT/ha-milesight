"""Constants for the Milesight integration."""

DOMAIN = "milesight"

CONF_JOIN_TOPIC = "join_topic"
CONF_UPLINK_TOPIC = "uplink_topic"
CONF_DOWNLINK_TOPIC = "downlink_topic"

# Topic pattern: milesight/{model}/{dev_eui}/{action}
DEFAULT_JOIN_TOPIC = "milesight/+/+/join"
DEFAULT_UPLINK_TOPIC = "milesight/+/+/uplink"
DEFAULT_DOWNLINK_TOPIC = "milesight/+/+/downlink"

PLATFORMS = ["sensor", "binary_sensor", "switch"]

# Dispatcher signals (formatted with entry_id / dev_eui at runtime)
SIGNAL_NEW_DEVICE = f"{DOMAIN}_new_device" + "_{entry_id}"
SIGNAL_DEVICE_UPDATED = f"{DOMAIN}_device_updated" + "_{entry_id}_{dev_eui}"
