"""Sensor entity descriptions and type constants for Eltako sensors."""
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
    UnitOfRatio,
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

DEFAULT_DEVICE_NAME_WINDOW_HANDLE = "Window handle"
DEFAULT_DEVICE_NAME_WEATHER_STATION = "Weather station"
DEFAULT_DEVICE_NAME_ELECTRICITY_METER = "Electricity meter"
DEFAULT_DEVICE_NAME_GAS_METER = "Gas meter"
DEFAULT_DEVICE_NAME_WATER_METER = "Water meter"
DEFAULT_DEVICE_NAME_HYGROSTAT = "Hygrostat"
DEFAULT_DEVICE_NAME_THERMOMETER = "Thermometer"
DEFAULT_DEVICE_NAME_CO2 = "CO2 sensor"
DEFAULT_DEVICE_NAME_AIR_QUAILTY_SENSOR = "Air Quality Sensor"

SENSOR_TYPE_BATTERY_VOLTAGE = "electricity_voltage"
SENSOR_TYPE_ELECTRICITY_CUMULATIVE = "electricity_cumulative"
SENSOR_TYPE_ELECTRICITY_CURRENT = "electricity_current"
SENSOR_TYPE_GAS_CUMULATIVE = "gas_cumulative"
SENSOR_TYPE_GAS_CURRENT = "gas_current"
SENSOR_TYPE_WATER_CUMULATIVE = "water_cumulative"
SENSOR_TYPE_WATER_CURRENT = "water_current"
SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_TEMPERATURE_CURRENT = "current_temperature"
SENSOR_TYPE_TARGET_TEMPERATURE = "target_temperature"
SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_CO2 = "co2"
SENSOR_TYPE_VOLTAGE = "voltage"
SENSOR_TYPE_PIR = "pir"
SENSOR_TYPE_WINDOWHANDLE = "windowhandle"
SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_DAWN = "weather_station_illuminance_dawn"
SENSOR_TYPE_WEATHER_STATION_TEMPERATURE = "weather_station_temperature"
SENSOR_TYPE_WEATHER_STATION_WIND_SPEED = "weather_station_wind_speed"
SENSOR_TYPE_WEATHER_STATION_RAIN = "weather_station_rain"
SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_WEST = "weather_station_illuminance_west"
SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_CENTRAL = "weather_station_illuminance_central"
SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_EAST = "weather_station_illuminance_east"
SENSOR_TYPE_ILLUMINANCE = "illuminance"


@dataclass
class EltakoSensorEntityDescription(SensorEntityDescription):
    """Describes Eltako sensor entity."""

SENSOR_DESC_BATTERY_VOLTAGE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_BATTERY_VOLTAGE,
    name="Battery Voltage",
    native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    icon="mdi:lightning-bolt",
    device_class=SensorDeviceClass.BATTERY,
    state_class=SensorStateClass.MEASUREMENT,
)

SENSOR_DESC_ELECTRICITY_CUMULATIVE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_ELECTRICITY_CUMULATIVE,
    name="Energy",
    native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    icon="mdi:lightning-bolt",
    device_class=SensorDeviceClass.ENERGY,
    state_class=SensorStateClass.TOTAL_INCREASING,
)

SENSOR_DESC_ELECTRICITY_CURRENT = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_ELECTRICITY_CURRENT,
    name="Power",
    native_unit_of_measurement=UnitOfPower.WATT,
    icon="mdi:lightning-bolt",
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_GAS_CUMULATIVE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_GAS_CUMULATIVE,
    name="Reading",
    native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    icon="mdi:fire",
    device_class=SensorDeviceClass.GAS,
    state_class=SensorStateClass.TOTAL_INCREASING,
)

SENSOR_DESC_GAS_CURRENT = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_GAS_CURRENT,
    name="Flow rate",
    native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    icon="mdi:fire",
    state_class=SensorStateClass.MEASUREMENT,
)

SENSOR_DESC_WATER_CUMULATIVE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WATER_CUMULATIVE,
    name="Reading",
    native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
    icon="mdi:water",
    device_class=SensorDeviceClass.WATER,
    state_class=SensorStateClass.TOTAL_INCREASING,
)

SENSOR_DESC_WATER_CURRENT = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WATER_CURRENT,
    name="Flow rate",
    native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    icon="mdi:water",
    state_class=SensorStateClass.MEASUREMENT,
)

SENSOR_DESC_WINDOWHANDLE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WINDOWHANDLE,
    name="Window handle",
    translation_key="windowhandle",
    icon="mdi:window-open-variant",
    device_class='window',
    native_unit_of_measurement=None,
    suggested_display_precision=None,
    suggested_unit_of_measurement=None,
    state_class=None
)

SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_DAWN = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_DAWN,
    name="Illuminance (dawn)",
    translation_key="weatherstation_dawn",
    native_unit_of_measurement=LIGHT_LUX,
    icon="mdi:weather-sunset",
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_WEATHER_STATION_TEMPERATURE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_TEMPERATURE,
    name="Temperature",
    translation_key="weatherstation_temp",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)

SENSOR_DESC_WEATHER_STATION_WIND_SPEED = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_WIND_SPEED,
    name="Wind speed",
    translation_key="weatherstatio_wind",
    native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    icon="mdi:windsock",
    device_class=SensorDeviceClass.WIND_SPEED,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)

SENSOR_DESC_WEATHER_STATION_RAIN = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_RAIN,
    name="Rain",
    translation_key="weatherstation_rain",
    native_unit_of_measurement="",
    icon="mdi:weather-pouring",
    device_class="rain",
    state_class=SensorStateClass.MEASUREMENT,
)

SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_WEST = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_WEST,
    name="Illuminance (west)",
    translation_key="weatherstation_illu_west",
    native_unit_of_measurement=LIGHT_LUX,
    icon="mdi:weather-sunny",
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_CENTRAL = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_CENTRAL,
    name="Illuminance (south)",
    translation_key="weatherstation_illu_south",
    native_unit_of_measurement=LIGHT_LUX,
    icon="mdi:weather-sunny",
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_WEATHER_STATION_ILLUMINANCE_EAST = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_WEATHER_STATION_ILLUMINANCE_EAST,
    name="Illuminance (east)",
    translation_key="weatherstation_illu_east",
    native_unit_of_measurement=LIGHT_LUX,
    icon="mdi:weather-sunny",
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_ILLUMINATION = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_ILLUMINANCE,
    name="Illuminance",
    native_unit_of_measurement=LIGHT_LUX,
    icon="mdi:sun-wireless-outline",
    device_class=SensorDeviceClass.ILLUMINANCE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_TEMPERATURE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_TEMPERATURE,
    name="Temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)

SENSOR_DESC_TEMPERATURE_CURRENT = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_TEMPERATURE_CURRENT,
    name="Current Temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)

SENSOR_DESC_TARGET_TEMPERATURE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_TARGET_TEMPERATURE,
    name="Target Temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    icon="mdi:thermometer",
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)

SENSOR_DESC_HUMIDITY = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_HUMIDITY,
    name="Humidity",
    native_unit_of_measurement=PERCENTAGE,
    icon="mdi:water-percent",
    device_class=SensorDeviceClass.HUMIDITY,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_TYPE_ACCELERATION = "acceleration"

def _acceleration_description(axis: str) -> "EltakoSensorEntityDescription":
    return EltakoSensorEntityDescription(
        key=f"{SENSOR_TYPE_ACCELERATION}_{axis}",
        name=f"Acceleration {axis.upper()}",
        native_unit_of_measurement="g",
        icon="mdi:axis-arrow",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    )

SENSOR_DESC_ACCELERATION_X = _acceleration_description("x")
SENSOR_DESC_ACCELERATION_Y = _acceleration_description("y")
SENSOR_DESC_ACCELERATION_Z = _acceleration_description("z")

SENSOR_DESC_CO2 = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_CO2,
    name="CO2",
    native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
    icon="mdi:molecule-co2",
    device_class=SensorDeviceClass.CO2,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
)

SENSOR_DESC_VOLTAGE = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_VOLTAGE,
    name="voltage",
    native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    icon="mdi:sine-wave",
    device_class=SensorDeviceClass.VOLTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
)

SENSOR_DESC_PIR = EltakoSensorEntityDescription(
    key=SENSOR_TYPE_PIR,
    name="pir",
    native_unit_of_measurement=None,
    icon="mdi:home-outline",
    device_class=None,
    state_class=SensorStateClass.MEASUREMENT,
)


