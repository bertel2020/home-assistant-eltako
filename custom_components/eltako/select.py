"""Select platform for Eltako."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
import json

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EXCLUDE, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from .device import *
from . import config_helpers
from .gateway import EnOceanGateway
from .const import *
from . import get_gateway_from_hass, get_device_config_for_gateway


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eltako select platform."""
    gateway: EnOceanGateway = get_gateway_from_hass(hass, config_entry)
    config: ConfigType = get_device_config_for_gateway(hass, config_entry, gateway)

    entities: list[EltakoEntity] = []
    
    platform = Platform.SELECT
    if platform in config:
        for entity_config in config[platform]:

            try:
                dev_conf = config_helpers.DeviceConf(entity_config)
                ###### Placeholder
                entities.append(EltakoSelectCoverAutomation(platform, gateway, dev_conf.id, dev_conf.name, dev_conf.eep))

            except Exception as e:
                LOGGER.warning("[%s] Could not load configuration", platform)
                LOGGER.critical(e, exc_info=True)

    # add select to cover devices
    if Platform.COVER in config:
        for entity_config in config[Platform.COVER]:
            try:
                dev_conf = config_helpers.DeviceConf(entity_config)
                entities.append(EltakoSelectCoverAutomation(platform, gateway, dev_conf.id, dev_conf.name, dev_conf.eep, current_option="Both", options=['Off', 'Morning', 'Evening', 'Both']))

            except Exception as e:
                LOGGER.warning("[%s] Could not load configuration", Platform.CLIMATE)
                LOGGER.critical(e, exc_info=True)


    async_add_entities(entities)




class AbstractSelect(EltakoEntity, SelectEntity, RestoreEntity):

    def load_value_initially(self, latest_state:State):
        try:
            if 'unknown' == latest_state.state:
                #LOGGER.debug(f"[{Platform.SELECT} {self.dev_id}] value initially loaded by 'unknown': [current_option: {self._attr_current_option}, state: {self.state}]")
                self._attr_current_option = self._attr_current_option
            else:
                if latest_state.state in ["Off", "Morning", "Evening", "Both"]:
                    #LOGGER.debug(f"[{Platform.SELECT} {self.dev_id}] value initially loaded by valid state: [current_option: {self._attr_current_option}, state: {self.state}]")
                    self._attr_current_option = latest_state.state
                else:
                    #LOGGER.debug(f"[{Platform.SELECT} {self.dev_id}] value initially loaded by unvalid state: [current_option: {self._attr_current_option}, state: {self.state}]")
                    self._attr_current_option = None
                
        except Exception as e:
            self._attr_current_option = None
            raise e
        
        self.schedule_update_ha_state()

        LOGGER.debug(f"[{Platform.SELECT} {self.dev_id}] value initially loaded: [current_option: {self._attr_current_option}, state: {self.state}]")




class EltakoSelectCoverAutomation(AbstractSelect):
    """Representation of an Eltako select entity for cover devices."""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, current_option: str | None, options: list[str]):
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = "automation mode"
        self.entity_description = SelectEntityDescription(
            key="automation_mode",
            name="Automation Mode",
            icon="mdi:form-select",
        )
        self._attr_current_option = current_option
        self._attr_options = options
        self._attr_translation_key = "cover_automation_mode"

        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep)
        LOGGER.debug(f"[{Platform.SELECT} {self.dev_id}] details: [current_option: {self._attr_current_option}, state: {self.state}, options: {self._attr_options}]")

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        self._attr_current_option = option
        self.async_write_ha_state()
