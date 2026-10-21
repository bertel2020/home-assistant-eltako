import asyncio
import unittest
from unittest import mock
from custom_components.eltako.sensor import *
from custom_components.eltako.binary_sensor import EltakoBinarySensor
from custom_components.eltako.sensor_descriptions import SENSOR_DESC_ACCELERATION_Y
from tests.mocks import *
from homeassistant.helpers.entity import Entity
from homeassistant.const import Platform
from eltakobus import *
from eltakobus.message import RegularVLDMessage, Regular4BSMessage

Entity.schedule_update_ha_state = mock.Mock(return_value=None)


def bits(*fields):
    value, total = 0, 0
    for field, size in fields:
        value = (value << size) | field
        total += size
    padded = (total + 7) // 8 * 8
    return (value << (padded - total)).to_bytes(padded // 8, "big")


ADDRESS = bytes.fromhex("05123456")
PAYLOAD = bits((500, 10), (100, 8), (12345, 17), (1, 2), (500, 10), (0, 10), (1000, 10), (1, 1), (0, 5))
MSG = RegularVLDMessage(ADDRESS, 0, PAYLOAD)


class TestVLDSensors(unittest.TestCase):
    dev_id = AddressExpression.parse("05-12-34-56")

    def setUp(self):
        # tests.mocks.HassMock calls asyncio.get_event_loop(), which Python 3.14 no longer creates implicitly
        asyncio.set_event_loop(asyncio.new_event_loop())

    def test_temperature_humidity_illumination_acceleration(self):
        eep = EEP.find("D2-14-41")
        sensors = {
            "temp": EltakoTemperatureSensor(Platform.SENSOR, GatewayMock(), self.dev_id, "n", eep),
            "hum": EltakoHumiditySensor(Platform.SENSOR, GatewayMock(), self.dev_id, "n", eep),
            "lux": EltakoIlluminationSensor(Platform.SENSOR, GatewayMock(), self.dev_id, "n", eep),
            "acc": EltakoAccelerationSensor(Platform.SENSOR, GatewayMock(), self.dev_id, "n", eep,
                                            SENSOR_DESC_ACCELERATION_Y, "acceleration_y"),
        }
        for s in sensors.values():
            s.value_changed(MSG)
        self.assertAlmostEqual(sensors["temp"].native_value, 10.0)
        self.assertEqual(sensors["hum"].native_value, 50.0)
        self.assertEqual(sensors["lux"].native_value, 12345.0)
        self.assertAlmostEqual(sensors["acc"].native_value, -2.5)

    def test_entity_forwards_vld_messages_for_its_address(self):
        s = EltakoTemperatureSensor(Platform.SENSOR, GatewayMock(), self.dev_id, "n", EEP.find("D2-14-40"))
        s._message_received_callback(MSG)
        self.assertAlmostEqual(s.native_value, 10.0)

    def test_a5_temperature_still_uses_current_temperature(self):
        s = EltakoTemperatureSensor(Platform.SENSOR, GatewayMock(), AddressExpression.parse("FF-FF-00-80"), "n", EEP.find("A5-04-02"))
        s.value_changed(Regular4BSMessage(address=b'\xFF\xFF\x00\x80', data=b'\x00\x7C\x86\x0F', status=0x00))
        self.assertEqual(s.native_value, 22.880000000000003)

    def test_contact_binary_sensor(self):
        from tests.test_binary_sensor_generic import TestBinarySensor
        bs = TestBinarySensor().create_binary_sensor(eep_string="D2-14-41", device_class="window", invert_signal=False)
        bs.value_changed(MSG)   # contact bit 1 = closed
        self.assertEqual(bs._attr_is_on, False)
        open_msg = RegularVLDMessage(ADDRESS, 0, bits((500, 10), (100, 8), (0, 17), (0, 2), (500, 10), (500, 10), (500, 10), (0, 1), (0, 5)))
        bs.value_changed(open_msg)
        self.assertEqual(bs._attr_is_on, True)

    def test_vld_eeps_are_accepted_by_schema(self):
        from custom_components.eltako.schema import SensorSchema, CONF_EEP_SUPPORTED_BINARY_SENSOR
        for e in ("D2-00-01", "D2-14-40", "D2-14-41"):
            self.assertIn(e, SensorSchema.CONF_EEP_SUPPORTED)
        self.assertIn("D2-14-41", CONF_EEP_SUPPORTED_BINARY_SENSOR)


if __name__ == "__main__":
    unittest.main()
