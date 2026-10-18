"""Additive diagnostics preserve existing entity IDs and sensor values."""
from types import SimpleNamespace
import unittest
from homeassistant.const import Platform
from eltakobus.util import AddressExpression
from custom_components.eltako.const import GatewayDeviceType
from custom_components.eltako.config_helpers import DEFAULT_GENERAL_SETTINGS
from custom_components.eltako.sensor import GatewayInfoField


class GatewayDiagnosticsTests(unittest.TestCase):
    def sensor(self, dev_type, key='Serial Path'):
        gateway = SimpleNamespace(hass=None, dev_id=7, dev_type=dev_type,
                                  base_id=AddressExpression.parse('FF-80-00-00'),
                                  serial_path='192.0.2.1', port=5100,
                                  general_settings=dict(DEFAULT_GENERAL_SETTINGS))
        return GatewayInfoField(Platform.SENSOR, gateway, key, gateway.serial_path)

    def test_lan_details_do_not_change_identity_or_value(self):
        sensor = self.sensor(GatewayDeviceType.LAN)
        self.assertEqual(sensor.unique_id, 'eltako_gw7_ff_80_00_00_serial_path')
        self.assertEqual(sensor.entity_id, 'sensor.eltako_gw7_ff_80_00_00_serial_path')
        self.assertEqual(sensor.native_value, '192.0.2.1')
        self.assertEqual(sensor.extra_state_attributes, {'host': '192.0.2.1', 'port': 5100})
        sensor.extra_state_attributes['port'] = 123
        self.assertEqual(sensor.extra_state_attributes['port'], 5100)

    def test_serial_gateway_and_other_fields_keep_attributes(self):
        self.assertIsNone(self.sensor(GatewayDeviceType.GatewayEltakoFAM14).extra_state_attributes)
        self.assertIsNone(self.sensor(GatewayDeviceType.LAN, 'Base Id').extra_state_attributes)
