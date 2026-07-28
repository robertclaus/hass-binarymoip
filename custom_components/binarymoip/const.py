"""Constants for the Binary MoIP integration."""

DOMAIN = "binarymoip"
DEVICES = "binarymoip_devices"


def power_on_key(name):
    """Options-flow / options-storage key for a receiver's power-on IR code."""
    return "{}: Power On Code".format(name)


def power_off_key(name):
    """Options-flow / options-storage key for a receiver's power-off IR code."""
    return "{}: Power Off Code".format(name)
