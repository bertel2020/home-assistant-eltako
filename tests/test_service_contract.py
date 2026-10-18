"""Exercise real service construction and compare complete outgoing telegrams."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from eltakobus.eep import A5_04_02, A5_10_06, F6_02_01
from custom_components.eltako.gateway import EnOceanGateway
from tools.generate_eep_params import ROOT, render_eep_params


class ServiceContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_preserves_fork_specific_payloads(self):
        gateway = object.__new__(EnOceanGateway)
        gateway.send_message = Mock()
        address = bytes.fromhex('FF800001')
        cases = (
            ('A5-04-02', dict(temperature=20, humidity=50, supply_voltage=3, learn_button=1), A5_04_02),
            ('F6-02-01', dict(rocker_first_action=1, energy_bow=1, rocker_second_action=0, second_action=0), F6_02_01),
        )
        for name, params, cls in cases:
            with self.subTest(eep=name):
                gateway.send_message.reset_mock()
                event = SimpleNamespace(service='gateway_7_send_message',
                                        data={'id': 'FF-80-00-01', 'eep': name, **params})
                await gateway.async_service_send_message(event, raise_exception=True)
                gateway.send_message.assert_called_once()
                actual = gateway.send_message.call_args.args[0]
                self.assertEqual(actual.serialize(), cls(**params).encode_message(address).serialize())

    async def test_existing_climate_service_enum_limitation_is_explicit(self):
        gateway = object.__new__(EnOceanGateway)
        gateway.send_message = Mock()
        event = SimpleNamespace(service='gateway_7_send_message', data={
            'id': 'FF-80-00-01', 'eep': 'A5-10-06',
            'mode': 1, 'priority': 0, 'target_temp': 22, 'current_temp': 20,
        })
        with self.assertLogs('eltako', level='ERROR'), self.assertRaises(AttributeError):
            await gateway.async_service_send_message(event, raise_exception=True)
        gateway.send_message.assert_not_called()

    async def test_parameter_documentation_matches_pinned_library(self):
        self.assertEqual((ROOT / 'docs/service-send-message/eep-params.md').read_text(), render_eep_params())
