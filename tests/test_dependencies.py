"""Dependency contract and hardware-free smoke checks.

Run separately from the legacy suite, whose modules patch global library APIs:
    python -m unittest discover -s tests -p test_dependencies.py -v
Install requirements.txt first for runtime checks (verified on HA 2026.10.2).
"""
import importlib
import importlib.metadata as metadata
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "custom_components/eltako/manifest.json").read_text())
HAS_HA = importlib.util.find_spec("homeassistant") is not None


class DependencyContractTests(unittest.TestCase):
    def test_development_requirements_include_exact_manifest_requirements(self):
        development = {
            line.strip() for line in (ROOT / "requirements.txt").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertTrue(set(MANIFEST["requirements"]) <= development)

    def test_own_libraries_use_immutable_archives_from_own_repositories(self):
        for name, repository in (("eltako14bus", "eltako14bus"),
                                 ("enocean", "enocean"),
                                 ("esp2-gateway-adapter", "esp2_gateway_adapter")):
            requirements = [r for r in MANIFEST["requirements"] if r.startswith(name + " @ ")]
            self.assertEqual(len(requirements), 1)
            url = urlparse(requirements[0].split(" @ ", 1)[1])
            self.assertEqual(url.scheme, "https")
            self.assertEqual(url.netloc, "github.com")
            self.assertRegex(url.path, rf"^/bertel2020/{repository}/archive/[0-9a-f]{{40}}\.zip$")


@unittest.skipUnless(HAS_HA, "Install requirements.txt for runtime smoke checks")
class RuntimeDependencyTests(unittest.TestCase):
    def test_installed_forks_match_the_manifest_sources(self):
        for name in ("eltako14bus", "enocean", "esp2-gateway-adapter"):
            dist = metadata.distribution(name)
            direct = json.loads(dist.read_text("direct_url.json"))
            requirement = next(r for r in MANIFEST["requirements"] if r.startswith(name + " @ "))
            self.assertEqual(direct["url"], requirement.split(" @ ", 1)[1])

    def test_all_manifest_requirements_are_satisfied(self):
        from packaging.requirements import Requirement

        for text in MANIFEST["requirements"]:
            requirement = Requirement(text)
            self.assertIn(metadata.version(requirement.name), requirement.specifier)

    def test_integration_and_all_configured_platforms_import(self):
        for module in ("eltakobus", "enocean.protocol.eep",
                       "esp2_gateway_adapter.esp3_serial_com",
                       "esp2_gateway_adapter.esp3_tcp_com",
                       "custom_components.eltako", "custom_components.eltako.config_flow"):
            with self.subTest(module=module):
                importlib.import_module(module)
        from custom_components.eltako.const import PLATFORMS

        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                importlib.import_module(f"custom_components.eltako.{platform}")

    def test_esp2_esp3_roundtrip_using_both_forks_and_adapter(self):
        from eltakobus.eep import F6_02_01, A5_38_08, CentralCommandDimming
        from esp2_gateway_adapter.esp3_serial_com import ESP3SerialCommunicator
        from enocean.protocol.packet import Packet

        address = bytes.fromhex("ff800001")
        messages = [
            F6_02_01(1, 1, 0, 0).encode_message(address),
            A5_38_08(command=2, dimming=CentralCommandDimming(50, 0, 1, 0, 0, 1)).encode_message(address),
        ]
        for message in messages:
            with self.subTest(message=type(message).__name__):
                packet = ESP3SerialCommunicator.convert_esp2_to_esp3_message(message)
                self.assertIsInstance(packet, Packet)
                self.assertGreater(len(packet.build()), 0)
                restored = ESP3SerialCommunicator.convert_esp3_to_esp2_message(packet)
                self.assertEqual(restored.data, message.data)
                self.assertEqual(restored.address, message.address)
                self.assertEqual(restored.status, message.status)
                if message.org == 0x07:
                    self.assertEqual(restored.serialize(), message.serialize())

    @unittest.expectedFailure
    def test_known_adapter_0_2_21_rps_output_is_parseable(self):
        """Known external adapter defect: RPS output lacks optional data.

        Keep visible as expected failure until the pinned adapter is repaired.
        A passing result becomes an unexpected success and prompts reassessment.
        """
        from eltakobus.eep import F6_02_01
        from esp2_gateway_adapter.esp3_serial_com import ESP3SerialCommunicator
        from enocean.protocol.packet import Packet

        message = F6_02_01(1, 1, 0, 0).encode_message(bytes.fromhex("ff800001"))
        outgoing = ESP3SerialCommunicator.convert_esp2_to_esp3_message(message)
        _, _, received = Packet.parse_msg(bytearray(outgoing.build()))
        self.assertIsNotNone(received)

    def test_enocean_eep_database_decodes_temperature(self):
        from enocean.protocol.packet import Packet

        telegram = bytearray.fromhex(
            "55 00 0A 07 01 EB A5 00 00 55 08 01 81 B7 44 00 "
            "01 FF FF FF FF 2D 00 75"
        )
        _, _, packet = Packet.parse_msg(telegram)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.parse_eep(0x02, 0x05), ["TMP"])
        self.assertAlmostEqual(packet.parsed["TMP"]["value"], 26.7, places=1)


if __name__ == "__main__":
    unittest.main()
