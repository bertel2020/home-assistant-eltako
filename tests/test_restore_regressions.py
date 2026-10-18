"""Restore regressions against real platform classes, without HA or bus writes."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from homeassistant.core import State
from homeassistant.const import Platform
from homeassistant.components.climate import HVACMode
from eltakobus.eep import A5_10_06, G5_3F_7F, H5_3F_7F
from eltakobus.util import AddressExpression
from custom_components.eltako.climate import ClimateController
from custom_components.eltako.cover import EltakoCover
from custom_components.eltako.config_helpers import DEFAULT_GENERAL_SETTINGS


class RestoreRegressionTests(unittest.TestCase):
    def entity(self, climate=False):
        gateway = SimpleNamespace(hass=None, dev_id=7,
                                  general_settings=dict(DEFAULT_GENERAL_SETTINGS))
        address = AddressExpression.parse('00-00-00-01')
        sender = AddressExpression.parse('FF-80-00-01')
        if climate:
            entity = ClimateController(Platform.CLIMATE, gateway, address, 'Room', A5_10_06,
                                       sender, A5_10_06, '°C', 16, 25,
                                       None, None, None, None, None, None, None)
        else:
            entity = EltakoCover(Platform.COVER, gateway, address, 'Blind', G5_3F_7F,
                                 sender, H5_3F_7F, 'blind', 10, 10, 15)
        entity.schedule_update_ha_state = Mock()
        entity.send_message = Mock()
        return entity

    def test_climate_restores_values_and_preserves_configured_modes(self):
        entity = self.entity(climate=True)
        modes = list(entity.hvac_modes)
        entity.load_value_initially(State('climate.room', 'heat', {
            'temperature': 22, 'current_temperature': 0, 'current_humidity': 45,
            'hvac_modes': ['off', 'cool'],
        }))
        self.assertEqual(entity.hvac_modes, modes)
        self.assertEqual(entity.hvac_mode, HVACMode.HEAT)
        self.assertEqual(entity.current_temperature, 0)
        self.assertEqual(entity.target_temperature, 22)
        self.assertEqual(entity.current_humidity, 45)
        entity.send_message.assert_not_called()

    def test_invalid_climate_values_do_not_abort_restore(self):
        for value in ('unknown', 'broken', float('nan'), float('inf'), True):
            with self.subTest(value=value):
                entity = self.entity(climate=True)
                with self.assertLogs('eltako', level='WARNING'):
                    entity.load_value_initially(State('climate.room', 'heat', {
                        'temperature': value, 'current_humidity': 40,
                    }))
                self.assertIsNone(entity.current_temperature)
                self.assertIsNone(entity.target_temperature)
                self.assertIsNone(entity.current_humidity)
                entity.schedule_update_ha_state.assert_called_once()
                entity.send_message.assert_not_called()

    def test_cover_intermediate_position_and_runtime_survive(self):
        entity = self.entity()
        unique_id = entity.unique_id
        entity.load_value_initially(State('cover.blind', 'open', {
            'current_position': 37, 'current_tilt_position': 12,
            'last_reported_runtime': 4.5, 'last_reported_direction': 'close',
        }))
        self.assertEqual(entity.current_cover_position, 37)
        self.assertEqual(entity.current_cover_tilt_position, 12)
        self.assertEqual(entity.extra_state_attributes['last_reported_runtime'], 4.5)
        self.assertEqual(entity.extra_state_attributes['last_reported_direction'], 'close')
        self.assertEqual(entity.unique_id, unique_id)
        entity.send_message.assert_not_called()

    def test_missing_legacy_cover_attributes_are_allowed(self):
        entity = self.entity()
        entity.load_value_initially(State('cover.blind', 'closed'))
        self.assertEqual(entity.current_cover_position, 0)
        self.assertIsNone(entity.extra_state_attributes['last_reported_runtime'])

    def test_invalid_cover_values_leave_unknown_state(self):
        for attributes in ({'current_position': 101}, {'current_tilt_position': -1},
                           {'last_reported_runtime': 'bad'}, {'current_position': float('nan')},
                           {'last_reported_direction': 'invalid'}):
            with self.subTest(attributes=attributes):
                entity = self.entity()
                with self.assertLogs('eltako', level='WARNING'):
                    entity.load_value_initially(State('cover.blind', 'open', attributes))
                self.assertIsNone(entity.current_cover_position)
                self.assertIsNone(entity.is_closed)
                entity.send_message.assert_not_called()
                # A later valid state can still be applied.
                entity.load_value_initially(State('cover.blind', 'open', {'current_position': 42}))
                self.assertEqual(entity.current_cover_position, 42)
