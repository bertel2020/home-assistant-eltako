"""Support for Eltako devices."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.reload import async_reload_integration_platforms
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er, device_registry as dr, entity_platform as pl

from .const import *
from .schema import CONFIG_SCHEMA
from . import config_helpers
from .gateway import *

LOG_PREFIX = "Eltako Integration Setup"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Eltako component."""
    return True

def print_config_entry(config_entry: ConfigEntry) -> None:
    LOGGER.debug("ConfigEntry")
    LOGGER.debug("- tilte: %s", config_entry.title)
    LOGGER.debug("- domain: %s", config_entry.domain)
    LOGGER.debug("- unique_id: %s", config_entry.unique_id)
    LOGGER.debug("- version: %s", config_entry.version)
    LOGGER.debug("- entry_id: %s", config_entry.entry_id)
    LOGGER.debug("- state: %s", config_entry.state)
    for k in config_entry.data.keys():
        LOGGER.debug("- data %s - %s", k, config_entry.data.get(k, ''))

type EltakoConfigEntry = ConfigEntry[EnOceanGateway]


def get_gateway_from_hass(hass: HomeAssistant, config_entry: EltakoConfigEntry) -> EnOceanGateway:
    """Return the gateway of a loaded config entry."""
    return config_entry.runtime_data


def get_device_config_for_gateway(hass: HomeAssistant, config_entry: ConfigEntry, gateway: EnOceanGateway) -> ConfigType:
    return config_helpers.get_device_config(hass.data[DATA_ELTAKO][ELTAKO_CONFIG], gateway.dev_id)


async def async_setup_entry(hass: HomeAssistant, config_entry: EltakoConfigEntry) -> bool:
    """Set up an Eltako gateway for the given entry."""
    LOGGER.info(f"[{LOG_PREFIX}] Start gateway setup.")
    # print_config_entry(config_entry)

    # Check domain
    if config_entry.domain != DOMAIN:
        LOGGER.warning("[%s] Received configuration entry of wrong domain '%s' (expected: '%s')!", LOG_PREFIX, config_entry.domain, DOMAIN)
        return False

    
    # Read the config
    config = await config_helpers.async_get_home_assistant_config(hass, CONFIG_SCHEMA)

    # Check if gateway ids are unique
    if not config_helpers.config_check_gateway(config):
        raise ConfigEntryError("Gateway ids in the configuration are not unique.")


    # set config for global access
    eltako_data = hass.data.setdefault(DATA_ELTAKO, {})
    eltako_data[ELTAKO_CONFIG] = config
    # print whole eltako configuration
    LOGGER.debug(f"config: {config}\n")

    general_settings = config_helpers.get_general_settings_from_configuration(hass)
    # Initialise the gateway
    # get base_id from user input
    if CONF_GATEWAY_DESCRIPTION not in config_entry.data.keys():
        raise ConfigEntryError("Device information for the gateway is not available. Try to delete and recreate the gateway.")
    gateway_description = config_entry.data[CONF_GATEWAY_DESCRIPTION]    # from user input
    if not ('(' in gateway_description and ')' in gateway_description):
        raise ConfigEntryError("No base id of the gateway available. Try to delete and recreate the gateway.")
    gateway_id = config_helpers.get_id_from_name(gateway_description)
    
    # get home assistant configuration section matching base_id
    gateway_config = await config_helpers.async_find_gateway_config_by_id(gateway_id, hass, CONFIG_SCHEMA)
    if not gateway_config:
        raise ConfigEntryError(f"No configuration for gateway id {gateway_id} found in 'configuration.yaml'.")
    
    # get serial path info
    if CONF_SERIAL_PATH not in config_entry.data.keys():
        raise ConfigEntryError("No information about the serial path available for the gateway.")
    gateway_serial_path = config_entry.data[CONF_SERIAL_PATH]

    # only transceiver can send teach-in telegrams
    gateway_device_type = GatewayDeviceType.find(gateway_config[CONF_DEVICE_TYPE])    # from configuration
    if gateway_device_type is None:
        raise ConfigEntryError(f"Gateway device type '{gateway_config[CONF_DEVICE_TYPE]}' is not supported.")
    if gateway_device_type == GatewayDeviceType.LAN:
        if gateway_config.get(CONF_GATEWAY_ADDRESS, None) is None:
            raise ConfigEntryError(f"Missing field '{CONF_GATEWAY_ADDRESS}' for LAN Gateway (id: {gateway_id})")

    general_settings[CONF_ENABLE_TEACH_IN_BUTTONS] = True # GatewayDeviceType.is_transceiver(gateway_device_type) # should only be disabled for decentral gateways

    LOGGER.info(f"[{LOG_PREFIX}] Initializes Gateway Device '{gateway_description}'")
    gateway_name = gateway_config.get(CONF_NAME, None)  # from configuration
    baud_rate= BAUD_RATE_DEVICE_TYPE_MAPPING[gateway_device_type]
    port = gateway_config.get(CONF_GATEWAY_PORT, 5100)
    auto_reconnect = gateway_config.get(CONF_GATEWAY_AUTO_RECONNECT, True)
    gateway_base_id = AddressExpression.parse(gateway_config[CONF_BASE_ID])
    message_delay = gateway_config.get(CONF_GATEWAY_MESSAGE_DELAY, None)
    LOGGER.debug(f"id: {gateway_id}, device type: {gateway_device_type}, serial path: {gateway_serial_path}, baud rate: {baud_rate}, base id: {gateway_base_id}")
    usb_gateway = EnOceanGateway(general_settings, hass, gateway_id, gateway_device_type, gateway_serial_path, baud_rate, port, gateway_base_id, gateway_name, auto_reconnect, message_delay, config_entry)

    
    await usb_gateway.async_setup()
    config_entry.runtime_data = usb_gateway

#    for platform in PLATFORMS:
#        hass.async_create_task(
#            hass.config_entries.async_forward_entry_setup(config_entry, platform)
#        )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: EltakoConfigEntry) -> bool:
    """Unload Eltako config entry."""

    gateway = get_gateway_from_hass(hass, config_entry)

    LOGGER.info("Unload %s and all its supported devices!", gateway.dev_name)
    if not await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS):
        return False

    await gateway.async_unload()
    return True





async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    dev_reg = dr.async_get(hass)
    dev_reg.async_update_device(
        device_id=device_entry.id,
        remove_config_entry_id=config_entry.entry_id,
    )
    LOGGER.debug("Device %s (%s) removed", device_entry.name, device_entry.id)
    return True
