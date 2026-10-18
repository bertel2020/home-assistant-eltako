"""Common base class for Eltako sensor entities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from eltakobus.util import AddressExpression, b2s
from eltakobus.eep import *
from eltakobus.message import ESP2Message

from . import config_helpers


from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    STATE_CLOSED,
    STATE_OPEN,
    LIGHT_LUX,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfEnergy,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
    Platform,
    PERCENTAGE,
    CONF_LANGUAGE,
    UnitOfElectricPotential,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import entity_registry as er

from .device import *
from .config_helpers import *
from .gateway import EnOceanGateway
from .const import *
from . import get_gateway_from_hass, get_device_config_for_gateway

from .sensor_descriptions import *


class EltakoSensor(EltakoEntity, RestoreEntity, SensorEntity):
    """Representation of an  Eltako sensor device such as a power meter."""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription) -> None:
        """Initialize the Eltako sensor device."""
        self.entity_description = description
        self._attr_state_class = description.state_class
        
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep)
        self._attr_native_value = None
        
    @property
    def name(self):
        """Return the default name for the sensor."""
        return self.entity_description.name

    def load_value_initially(self, latest_state:State):
        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] eneity unique_id: {self.unique_id}")
        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] latest state - state: {latest_state.state}")
        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id}] latest state - attributes: {latest_state.attributes}")
        try:
            if 'unknown' == latest_state.state:
                self._attr_is_on = None
            else:
                if latest_state.attributes.get('state_class', None) == 'measurement':
                    if latest_state.state.count('.') + latest_state.state.count(',') == 1:
                        self._attr_native_value = float(latest_state.state)
                    elif latest_state.state.count('.') == 0 and latest_state.state.count(',') == 0:
                        self._attr_native_value = int(latest_state.state)
                    else:
                        self._attr_native_value = None

                elif latest_state.attributes.get('state_class', None) == 'total_increasing':
                    if latest_state.state.count('.') + latest_state.state.count(',') == 1:
                        self._attr_native_value = float(latest_state.state)
                    elif latest_state.state.count('.') == 0 and latest_state.state.count(',') == 0:
                        self._attr_native_value = int(latest_state.state)
                    else:
                        self._attr_native_value = None

                elif latest_state.attributes.get('device_class', None) == 'window':
                    self._attr_native_value = latest_state.state

                elif latest_state.attributes.get('device_class', None) == 'device_class':
                    # e.g.: 2024-02-12T23:32:44+00:00
                    self._attr_native_value = datetime.strptime(latest_state.state, '%Y-%m-%dT%H:%M:%S%z:%f')
            
        except Exception as e:
            if hasattr(self, '_attr_is_on'):
                self._attr_is_on = None
            elif hasattr(self, '_attr_native_value'):
                self._attr_native_value = None
            raise e
        
        self.schedule_update_ha_state()

        LOGGER.debug(f"[{self._attr_ha_platform} {self.dev_id} ({type(self).__name__})] value initially loaded: [native_value: {self.native_value}, state: {self.state}]")        

