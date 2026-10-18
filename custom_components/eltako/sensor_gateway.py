"""Sensors that expose gateway diagnostics and static information."""
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
from .sensor_base import *


class GatewayLastReceivedMessage(EltakoSensor):
    """Protocols last time when message received"""

    def __init__(self, platform: str, gateway: EnOceanGateway):
        super().__init__(platform, gateway,
                         dev_id=gateway.base_id, 
                         dev_name="Last Message Received", 
                         dev_eep=None,
                         description=EltakoSensorEntityDescription(
                            key="Last Message Received",
                            name="Last Message Received",
                            icon="mdi:message-check-outline",
                            device_class=SensorDeviceClass.TIMESTAMP,
                            has_entity_name= True,
                        )
        )
        self._attr_name = "Last Message Received"
        self.gateway.set_last_message_received_handler(self.async_value_changed)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.gateway.serial_path)},
            name= self.gateway.dev_name,
            manufacturer=MANUFACTURER,
            model=self.gateway.model,
            via_device=(DOMAIN, self.gateway.serial_path)
        )
    
    async def async_value_changed(self, value: datetime) -> None:
        try:
            self.value_changed(value)
        except AttributeError as e:
            # Home Assistant not ready yet
            pass  

    def value_changed(self, value: datetime) -> None:
        """Update the current value."""
        # LOGGER.debug("[%s] Last message received", Platform.SENSOR)

        if isinstance(value, datetime):
            self.native_value = value
            self.schedule_update_ha_state()

class GatewayReceivedMessagesInActiveSession(EltakoSensor):
    """Protocols amount of messages per session"""

    def __init__(self, platform: str, gateway: EnOceanGateway):
        super().__init__(platform, gateway,
                         dev_id=gateway.base_id, 
                         dev_name="Received Messages per Session", 
                         dev_eep=None,
                         description=EltakoSensorEntityDescription(
                            key="Received Messages per Session",
                            name="Received Messages per Session",
                            state_class=SensorStateClass.TOTAL_INCREASING,
                            # device_class=SensorDeviceClass.VOLUME,
                            # native_unit_of_measurement="Messages", # => raises error message
                            unit_of_measurement=None,
                            suggested_unit_of_measurement=None,
                            icon="mdi:chart-line",
                        )
        )
        self._attr_name="Received Messages per Session"
        self.gateway.set_received_message_count_handler(self.async_value_changed)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.gateway.serial_path)},
            name= self.gateway.dev_name,
            manufacturer=MANUFACTURER,
            model=self.gateway.model,
            via_device=(DOMAIN, self.gateway.serial_path)
        )
    
    async def async_value_changed(self, value: int) -> None:
        try:
            self.value_changed(value)
        except AttributeError as e:
            # Home Assistant not ready yet
            pass  

    def value_changed(self, value: int) -> None:
        """Update the current value."""
        # LOGGER.debug("[%s] received amount of messages: %s", Platform.SENSOR, str(value))

        self.native_value = value
        self.schedule_update_ha_state()


class StaticInfoField(EltakoSensor):
    """Key value fields for gateway information"""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, key:str, value:str, icon:str=None):
        super().__init__(platform, gateway,
                         dev_id=dev_id, 
                         dev_name=dev_name, 
                         dev_eep=dev_eep,
                         description=EltakoSensorEntityDescription(
                            key=key,
                            name=key,
                            icon=icon,
                            has_entity_name= True,
                        )
        )
        self._attr_name = key
        self._attr_native_value = value

    def value_changed(self, value) -> None:
        pass

class GatewayInfoField(StaticInfoField):
    """Key value fields for gateway information"""

    def __init__(self, platform: str, gateway: EnOceanGateway, key:str, value:str, icon:str=None):
        super().__init__(platform, 
                         gateway,
                         dev_id=gateway.base_id, 
                         dev_name=key, 
                         dev_eep=None,
                         key=key,
                         value=value,
                         icon=icon
                         )
        
    @property
    def extra_state_attributes(self):
        """Expose LAN connection details without changing the existing sensor ID/value."""
        if self.entity_description.key == "Serial Path" and GatewayDeviceType.is_lan_gateway(self.gateway.dev_type):
            return {"host": self.gateway.serial_path, "port": self.gateway.port}
        return super().extra_state_attributes

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.gateway.serial_path)},
            name= self.gateway.dev_name,
            manufacturer=MANUFACTURER,
            model=self.gateway.model,
            via_device=(DOMAIN, self.gateway.serial_path)
        )
        
class EventListenerInfoField(EltakoSensor):
    """Key value fields for gateway information"""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, event_id: str, key:str, convert_event_function, icon:str=None):
        super().__init__(platform, gateway,
                         dev_id=dev_id, 
                         dev_name=dev_name, 
                         dev_eep=dev_eep,
                         description=EltakoSensorEntityDescription(
                            key=key,
                            name=key,
                            icon=icon,
                            has_entity_name= True,
                        )
        )
        self.convert_event_function = convert_event_function
        self._attr_name = key
        self._attr_native_value = ''
        self.listen_to_addresses.clear()

        LOGGER.debug(f"[{platform}] [{EventListenerInfoField.__name__}] [{b2s(dev_id[0])}] [{key}] Register event: {event_id}")
        self.hass.bus.async_listen(event_id, self.value_changed)

    
    def value_changed(self, event) -> None:
        LOGGER.debug(f"Received event: {event}")
        self.native_value = self.convert_event_function(event)

        self.schedule_update_ha_state()








