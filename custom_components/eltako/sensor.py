"""Support for Eltako sensors."""
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
from .sensor_gateway import *


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eltako sensor device."""
    gateway: EnOceanGateway = get_gateway_from_hass(hass, config_entry)
    config: ConfigType = get_device_config_for_gateway(hass, config_entry, gateway)

    entities: list[EltakoEntity] = []
    
    platform = Platform.SENSOR
    if platform in config:
        for entity_config in config[platform]:
            try:
                dev_conf = DeviceConf(entity_config, [CONF_METER_TARIFFS, CONF_INVERT_SIGNAL])
                dev_name = dev_conf.name
            
                if dev_conf.eep in [A5_13_01]:
                    if dev_name == dev_conf.name:
                        dev_name = DEFAULT_DEVICE_NAME_WEATHER_STATION
                    
                    entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_DAWN))
                    entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_TEMPERATURE))
                    entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_WIND_SPEED))
                    #entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_RAIN))
                    entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_WEST))
                    entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_CENTRAL))
                    entities.append(EltakoWeatherStation(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_EAST))
                    
                elif dev_conf.eep in [F6_10_00]:
                    if dev_name == "":
                        dev_name = DEFAULT_DEVICE_NAME_WINDOW_HANDLE
                    
                    entities.append(EltakoWindowHandle(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WINDOWHANDLE, dev_conf.get(CONF_INVERT_SIGNAL)))
                    
                elif dev_conf.eep in [A5_12_01]:
                    if dev_name == "":
                        dev_name = DEFAULT_DEVICE_NAME_ELECTRICITY_METER
                    
                    for tariff in dev_conf.get(CONF_METER_TARIFFS, []):
                        entities.append(EltakoMeterSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_ELECTRICITY_CUMULATIVE, tariff=(tariff - 1)))
                    _tariff_in_name = dev_conf.get(CONF_METER_TARIFFS, []) != []
                    entities.append(EltakoMeterSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_ELECTRICITY_CURRENT, tariff=0, tariff_in_name=_tariff_in_name))

                elif dev_conf.eep in [A5_12_02]:
                    if dev_name == "":
                        dev_name = DEFAULT_DEVICE_NAME_GAS_METER
                        
                    for tariff in dev_conf.get(CONF_METER_TARIFFS, []):
                        entities.append(EltakoMeterSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_GAS_CUMULATIVE, tariff=(tariff - 1)))
                        entities.append(EltakoMeterSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_GAS_CURRENT, tariff=(tariff - 1)))

                elif dev_conf.eep in [A5_12_03]:
                    if dev_name == "":
                        dev_name = DEFAULT_DEVICE_NAME_WATER_METER
                        
                    for tariff in dev_conf.get(CONF_METER_TARIFFS, []):
                        entities.append(EltakoMeterSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WATER_CUMULATIVE, tariff=(tariff - 1)))
                        entities.append(EltakoMeterSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, SENSOR_DESC_WATER_CURRENT, tariff=(tariff - 1)))

                elif dev_conf.eep in [A5_04_01, A5_04_02, A5_04_03, A5_10_12]:
                    
                    entities.append(EltakoTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoHumiditySensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoBatteryVoltageSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    if dev_conf.eep in [A5_10_12]:
                        entities.append(EltakoTargetTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))

                elif dev_conf.eep in [A5_10_06, A5_10_03]:
                    entities.append(EltakoTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoTargetTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))

                elif dev_conf.eep in [A5_09_04]:
                    entities.append(EltakoTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoHumiditySensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoCO2Sensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                
                elif dev_conf.eep in [D2_00_01, D2_14_40, D2_14_41]:
                    # VLD (RORG D2) sensors, received via ESP3 gateways only
                    entities.append(EltakoTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoHumiditySensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoIlluminationSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    if dev_conf.eep in [D2_14_40, D2_14_41]:
                        for description, attribute in ((SENSOR_DESC_ACCELERATION_X, "acceleration_x"),
                                                       (SENSOR_DESC_ACCELERATION_Y, "acceleration_y"),
                                                       (SENSOR_DESC_ACCELERATION_Z, "acceleration_z")):
                            entities.append(EltakoAccelerationSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, description, attribute))

                elif dev_conf.eep in [A5_09_0C]:
                ### Eltako FLGTF only supports VOCT Total
                    for t in VOC_SubstancesType:
                        if t.index in entity_config[CONF_VOC_TYPE_INDEXES]:
                            entities.append(EltakoAirQualitySensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, t, entity_config[CONF_LANGUAGE]))

                elif dev_conf.eep in [A5_07_01]:
                    entities.append(EltakoPirSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoVoltageSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))

                elif dev_conf.eep in [A5_08_01]:
                    entities.append(EltakoTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoIlluminationSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    entities.append(EltakoBatteryVoltageSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    # _pir_status => as binary sensor

                elif dev_conf.eep in [A5_06_01]:
                    entities.append(EltakoIlluminationSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))
                    #TODO: add twilight
                    #TODO: add daylight
                    # both are currently combined in illumination

            except Exception as e:
                LOGGER.warning("[%s] Could not load configuration", platform)
                LOGGER.critical(e, exc_info=True)

    # add labels for buttons
    if Platform.BINARY_SENSOR in config:
        for entity_config in config[Platform.BINARY_SENSOR]:
            try:
                dev_conf = DeviceConf(entity_config)
                if dev_conf.eep in [F6_01_01, F6_02_01, F6_02_02]:
                    def convert_event(event):
                        # if hasattr(event, 'data') and isinstance(event.data, dict) and 'pressed_buttons' in event.data:
                        return config_helpers.button_abbreviation_to_str(event.data['pressed_buttons'])

                    event_id = config_helpers.get_bus_event_type(gateway.dev_id, EVENT_BUTTON_PRESSED, dev_conf.id)
                    if dev_conf.eep in [F6_02_01, F6_02_02]:
                        entities.append(EventListenerInfoField(platform, gateway, dev_conf.id, dev_conf.name, dev_conf.eep, event_id, "Pushed Buttons", convert_event, "mdi:gesture-tap-button"))

                    entities.append(StaticInfoField(platform, gateway, dev_conf.id, dev_conf.name, dev_conf.eep, "Event Id", event_id, "mdi:form-textbox"))
            
            except Exception as e:
                LOGGER.warning("[%s] Could not load configuration", Platform.BINARY_SENSOR)
                LOGGER.critical(e, exc_info=True)

    # add id field for every device
    for pl in PLATFORMS:
        if pl in config:
            for entity_config in config[pl]:
                try:
                    dev_conf = DeviceConf(entity_config)
                    entities.append(StaticInfoField(platform, gateway, dev_conf.id, dev_conf.name, dev_conf.eep, "Id", b2s(dev_conf.id[0]), "mdi:identifier"))
                
                except Exception as e:
                    LOGGER.warning("[%s] Could not load configuration", Platform.BINARY_SENSOR)
                    LOGGER.critical(e, exc_info=True)



    # add meter and hygrostat to climate devices
    if Platform.CLIMATE in config:
        for entity_config in config[Platform.CLIMATE]:
            try:
                dev_conf = DeviceConf(entity_config)
                actuator_meter = config_helpers.get_device_conf(entity_config, CONF_ROOM_ACTUATOR_METER)
                hygrostat = config_helpers.get_device_conf(entity_config, CONF_ROOM_HYGROSTAT)

                if actuator_meter:
                    entities.append(EltakoMeterSensorForClimate(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, actuator_meter, SENSOR_DESC_ELECTRICITY_CUMULATIVE))
                    entities.append(EltakoMeterSensorForClimate(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, actuator_meter, SENSOR_DESC_ELECTRICITY_CURRENT))

                if hygrostat:
                    entities.append(EltakoHumiditySensorForClimate(platform, gateway, dev_conf.id, dev_name, dev_conf.eep, hygrostat))
                    entities.append(EltakoTemperatureSensor(platform, gateway, dev_conf.id, dev_name, dev_conf.eep))

            except Exception as e:
                LOGGER.warning("[%s] Could not load configuration", Platform.CLIMATE)
                LOGGER.critical(e, exc_info=True)





    # add gateway information
    entities.append(GatewayInfoField(platform, gateway, "Id", str(gateway.dev_id), "mdi:identifier"))
    entities.append(GatewayInfoField(platform, gateway, "Base Id", b2s(gateway.base_id[0]), "mdi:identifier"))
    entities.append(GatewayInfoField(platform, gateway, "Serial Path", gateway.serial_path, "mdi:usb"))
    entities.append(GatewayInfoField(platform, gateway, "USB Protocol", gateway.native_protocol, "mdi:usb"))
    entities.append(GatewayInfoField(platform, gateway, "Message Delay", gateway.message_delay, "mdi:av-timer"))
    entities.append(GatewayInfoField(platform, gateway, "Auto Connect Enabled", gateway.is_auto_reconnect_enabled, "mdi:connection"))
    entities.append(GatewayLastReceivedMessage(platform, gateway))
    entities.append(GatewayReceivedMessagesInActiveSession(platform, gateway))

    validate_actuators_dev_and_sender_id(entities)
    log_entities_to_be_added(entities, platform)
    async_add_entities(entities)


class EltakoPirSensor(EltakoSensor):
    """Occupancy Sensor"""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep:EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_PIR) -> None:
        """Initialize the Eltako meter sensor device."""
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep, description)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded:A5_07_01 = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Motion Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = decoded.pir_status

        self.schedule_update_ha_state()


class EltakoVoltageSensor(EltakoSensor):
    """Voltage Sensor"""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep:EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_VOLTAGE) -> None:
        """Initialize the Eltako meter sensor device."""
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep, description)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded:A5_07_01 = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Voltage Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = decoded.support_voltage

        self.schedule_update_ha_state()


class EltakoMeterSensor(EltakoSensor):
    """Representation of an Eltako electricity sensor.
    EEPs (EnOcean Equipment Profiles):
    - A5-12-01 (Automated Meter Reading, Electricity)
    - A5-12-02 (Automated Meter Reading, Gas)
    - A5-12-03 (Automated Meter Reading, Water)
    """
    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep:EEP, description: EltakoSensorEntityDescription, *, tariff, tariff_in_name:bool=True) -> None:
        """Initialize the Eltako meter sensor device."""
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep, description)
        self._tariff = tariff
        self._tariff_in_name = tariff_in_name

    @property
    def name(self):
        """Return the default name for the sensor."""
        if self._tariff_in_name:
            return f"{self.entity_description.name} (Tariff {self._tariff + 1})"
        else:
            return f"{self.entity_description.name}"

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor.
        For cumulative values, we alway respect the channel.
        For current values, we respect the channel just for gas and water.
        """
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Meter Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        if decoded.learn_button != 1:
            return
        
        tariff = decoded.measurement_channel
        cumulative = not decoded.data_type
        value = decoded.meter_reading
        divisor = 10 ** decoded.divisor
        calculatedValue = value / divisor
        
        if cumulative and self._tariff == tariff and (
            self.entity_description.key == SENSOR_TYPE_ELECTRICITY_CUMULATIVE or
            self.entity_description.key == SENSOR_TYPE_GAS_CUMULATIVE or
            self.entity_description.key == SENSOR_TYPE_WATER_CUMULATIVE):
            self._attr_native_value = round(calculatedValue, 2)
            self.schedule_update_ha_state()
        elif (not cumulative) and msg.data[3] != 0x8F and self.entity_description.key == SENSOR_TYPE_ELECTRICITY_CURRENT: # 0x8F means that, it's sending the serial number of the meter
            self._attr_native_value = round(calculatedValue, 2)
            self.schedule_update_ha_state()
        elif (not cumulative) and self._tariff == tariff and (
            self.entity_description.key == SENSOR_TYPE_GAS_CURRENT or
            self.entity_description.key == SENSOR_TYPE_WATER_CURRENT):
            # l/s -> m3/h
            self._attr_native_value = round(calculatedValue * 3.6, 2)
            self.schedule_update_ha_state()


class EltakoWindowHandle(EltakoSensor):
    """Representation of an Eltako window handle device.
    EEPs (EnOcean Equipment Profiles):
    - F6-10-00 (Mechanical handle / Hoppe AG)
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription, invert_signal: bool) -> None:
        """Initialize the Eltako window handle sensor device."""
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep, description)
        self.invert_signal = invert_signal

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded:F6_10_00 = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Window Handle Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        if decoded.handle_position == WindowHandlePosition.CLOSED:
            if not self.invert_signal:
                self._attr_native_value = STATE_CLOSED
            else:
                self._attr_native_value = "tilt"
        elif decoded.handle_position == WindowHandlePosition.OPEN:
            self._attr_native_value = STATE_OPEN
        elif decoded.handle_position == WindowHandlePosition.TILT:
            if not self.invert_signal:
                self._attr_native_value = "tilt"
            else:
                self._attr_native_value = STATE_CLOSED
        else:
            return

        self.schedule_update_ha_state()


class EltakoWeatherStation(EltakoSensor):
    """Representation of an Eltako weather station.
    EEPs (EnOcean Equipment Profiles):
    - A5-13-01 (Weather station)
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription) -> None:
        """Initialize the Eltako weather station device."""
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep, description)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Weather Station %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        if decoded.learn_button != 1:
            return
        
        if msg.data == bytes((0, 0, 0xFF, 0x1A)): # I don't really know why this is filtered out
            return

        if self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_DAWN:
            if decoded.identifier != 0x01:
                return
            
            self._attr_native_value = decoded.dawn_sensor
        
        elif self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_TEMPERATURE:
            if decoded.identifier != 0x01:
                return
            
            LOGGER.debug(f"[EltakoWeatherStation] received message - temperature: {decoded.temperature}")
            self._attr_native_value = round((decoded.temperature * 2), 0) / 2
        
        elif self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_WIND_SPEED:
            if decoded.identifier != 0x01:
                return
            
            self._attr_native_value = decoded.wind_speed

        ### RAIN Sensor as Binary Sensor in binary_sensor.py
        #elif self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_RAIN:
        #    if decoded.identifier != 0x01:
        #        return
        #    
        #    self._attr_native_value = decoded.rain_indication

        elif self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_WEST:
            if decoded.identifier != 0x02:
                return
            
            self._attr_native_value = decoded.sun_west * 1000.0
        
        elif self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_CENTRAL:
            if decoded.identifier != 0x02:
                return
            
            self._attr_native_value = decoded.sun_south * 1000.0
        
        elif self.entity_description.key == SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_EAST:
            if decoded.identifier != 0x02:
                return
            
            self._attr_native_value = decoded.sun_east * 1000.0

        self.schedule_update_ha_state()


class EltakoTemperatureSensor(EltakoSensor):
    """Representation of an Eltako temperature sensor.
    EEPs (EnOcean Equipment Profiles):
    - A5-04-02 (Temperature and Humidity)
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_TEMPERATURE) -> None:
        """Initialize the Eltako temperature sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_THERMOMETER
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Temperature Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        # VLD profiles (D2-xx-xx) only provide `temperature`
        self._attr_native_value = decoded.current_temperature if hasattr(decoded, "current_temperature") else decoded.temperature

        self.schedule_update_ha_state()

class EltakoAccelerationSensor(EltakoSensor):
    """Representation of one acceleration axis of a VLD multisensor.
    EEPs (EnOcean Equipment Profiles):
    - D2-14-40, D2-14-41
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription, attribute: str) -> None:
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_THERMOMETER
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)
        self._attribute = attribute

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Acceleration Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return

        self._attr_native_value = getattr(decoded, self._attribute)

        self.schedule_update_ha_state()


class EltakoIlluminationSensor(EltakoSensor):
    """Brightness sensor"""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_ILLUMINATION) -> None:
        """Initialize the Eltako temperature sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_THERMOMETER
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Illumination Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = decoded.illumination

        self.schedule_update_ha_state()


class EltakoBatteryVoltageSensor(EltakoSensor):
    """Representation of an Eltako battery sensor."""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_BATTERY_VOLTAGE) -> None:
        """Initialize the Eltako temperature sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = "Battery Sensor"
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)

    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Battery Voltage Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = decoded.supply_voltage

        self.schedule_update_ha_state()


class EltakoTargetTemperatureSensor(EltakoSensor):
    """Representation of an Eltako target temperature sensor.
    EEPs (EnOcean Equipment Profiles):
    - A5-10-06, A5-10-12
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_TARGET_TEMPERATURE) -> None:
        """Initialize the Eltako temperature sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_THERMOMETER
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)
    
    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Target Temperature Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = round(2 * decoded.target_temperature, 0) / 2

        self.schedule_update_ha_state()


class EltakoHumiditySensor(EltakoSensor):
    """Representation of an Eltako humidity sensor.
    EEPs (EnOcean Equipment Profiles):
    - A5-04-02 (Temperature and Humidity)
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep: EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_HUMIDITY) -> None:
        """Initialize the Eltako humidity sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_HYGROSTAT
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)
    
    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Humidity Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = decoded.humidity

        self.schedule_update_ha_state()






class EltakoCO2Sensor(EltakoSensor):
    """Representation of an Eltako CO2 sensor.
    EEPs (EnOcean Equipment Profiles):
    - A5-09-04 (CO2, Temperature and Humidity)
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep: EEP, description: EltakoSensorEntityDescription=SENSOR_DESC_CO2) -> None:
        """Initialize the Eltako CO2 sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_CO2
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)
    
    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[CO2 Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        self._attr_native_value = decoded.concentration

        self.schedule_update_ha_state()





class EltakoAirQualitySensor(EltakoSensor):
    """Representation of an Eltako air quality sensor.
    
    EEPs (EnOcean Equipment Profiles):
    - A5-09-0C
    """

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name: str, dev_eep: EEP, voc_type:VOC_SubstancesType, language:LANGUAGE_ABBREVIATION) -> None:
        """Initialize the Eltako air quality sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_THERMOMETER

        self.voc_type_name = voc_type.name_en
        if language == LANGUAGE_ABBREVIATION.LANG_GERMAN:
            self.voc_type_name = voc_type.name_de

        description = EltakoSensorEntityDescription(
            key = "air_quality_sensor_"+self.voc_type_name,
            device_class = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
            # device_class=SensorDeviceClass.AQI,
            name = self.voc_type_name,
            native_unit_of_measurement = voc_type.unit,
            icon="mdi:air-filter",
            state_class=SensorStateClass.MEASUREMENT,
        )

        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)
        self.voc_type = voc_type
        # self._attr_suggested_unit_of_measurement = voc_type.unit

        LOGGER.debug(f"entity_description: {self.entity_description}, voc_type: {voc_type}")
    
    
    def value_changed(self, msg: ESP2Message):
        """Update the internal state of the sensor."""
        try:
            decoded = self.dev_eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning("[Air Quality Sensor %s] Could not decode message: %s", self.dev_id, str(e))
            return
        
        if decoded.voc_type.index == self.voc_type.index:
            # LOGGER.debug(f"[EltakoAirQualitySensor] received message - concentration: {decoded.concentration}, voc_type: {decoded.voc_type}, voc_unit: {decoded.voc_unit}")
            self._attr_native_value = decoded.concentration

        self.schedule_update_ha_state()


class EltakoMeterSensorForClimate(EltakoSensor):
    """Representation of an Eltako electricity sensor."""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep:EEP, actuator_meter, description: EltakoSensorEntityDescription) -> None:
        """Initialize the Eltako meter sensor device."""
        super().__init__(platform, gateway, dev_id, dev_name, dev_eep, description)

        self.actuator_meter = actuator_meter
        if self.actuator_meter:
            LOGGER.debug(f"[climate/sensor {self.dev_id}] Actuator meter found: {self.actuator_meter.id[0]}")
            #LOGGER.debug(f"[climate {self.dev_id}] Actuator details: {self.actuator}")
            self.listen_to_addresses.append(self.actuator_meter.id[0])

    @property
    def name(self):
        """Return the default name for the sensor."""
        return f"{self.entity_description.name}"

    def value_changed(self, msg: ESP2Message):

        if self.actuator_meter:
            actuator_meter_address = self.actuator_meter.id[0]
            if msg.address == actuator_meter_address:
                LOGGER.debug(f"[climate/sensor {self.dev_id}] Change state triggered by actuator meter: {self.actuator_meter.id}")
                self.change_actuator_meter_values(msg)


    def change_actuator_meter_values(self, msg: ESP2Message) -> None:
        try:
            decoded = self.actuator_meter.eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning(f"[climate/sensor {self.dev_id}] Could not decode message: %s", str(e))
            return
        
        if decoded.learn_button != 1:
            return

        cumulative = not decoded.data_type
        value = decoded.meter_reading
        divisor = 10 ** decoded.divisor
        calculatedValue = value / divisor
        
        if cumulative and self.entity_description.key == SENSOR_TYPE_ELECTRICITY_CUMULATIVE:
            self._attr_native_value = round(calculatedValue, 2)
            self.schedule_update_ha_state()
        elif (not cumulative) and msg.data[3] != 0x8F and self.entity_description.key == SENSOR_TYPE_ELECTRICITY_CURRENT: # 0x8F means that, it's sending the serial number of the meter
            self._attr_native_value = round(calculatedValue, 2)
            self.schedule_update_ha_state()



class EltakoHumiditySensorForClimate(EltakoSensor):
    """Representation of an Eltako humidity sensor."""

    def __init__(self, platform: str, gateway: EnOceanGateway, dev_id: AddressExpression, dev_name:str, dev_eep: EEP, hygrostat, description: EltakoSensorEntityDescription=SENSOR_DESC_HUMIDITY) -> None:
        """Initialize the Eltako humidity sensor."""
        _dev_name = dev_name
        if _dev_name == "":
            _dev_name = DEFAULT_DEVICE_NAME_HYGROSTAT
        super().__init__(platform, gateway, dev_id, _dev_name, dev_eep, description)

        self.hygrostat = hygrostat
        if self.hygrostat:
            LOGGER.debug(f"[climate/sensor {self.dev_id}] Hygrostat found: {self.hygrostat.id[0]}")
            #LOGGER.debug(f"[climate {self.dev_id}] Actuator details: {self.actuator}")
            self.listen_to_addresses.append(self.hygrostat.id[0])


    def value_changed(self, msg: ESP2Message):

        if self.hygrostat:
            hygrostat_address = self.hygrostat.id[0]
            if msg.address == hygrostat_address:
                LOGGER.debug(f"[climate/sensor {self.dev_id}] Change state triggered by hygrostat: {self.hygrostat.id[0]}")
                self.change_hygrostat_values(msg)

    def change_hygrostat_values(self, msg: ESP2Message) -> None:
        try:
            if msg.data[3] == 0x08:
                decoded = self.hygrostat.eep.decode_message(msg)
        except Exception as e:
            LOGGER.warning(f"[climate/sensor {self.dev_id}] Could not decode message: %s", str(e))
            return
        
        self._attr_native_value = decoded.humidity
        self.schedule_update_ha_state()


