"""Gateway descriptions created before v1.3.4 contain 'ESP2' and must match the current naming."""
import unittest

from custom_components.eltako import config_helpers


class GatewayDescriptionTests(unittest.TestCase):
    def test_old_description_is_mapped_to_current_naming(self):
        old = "EnOcean ESP2 Gateway - fam14 (Id: 1, BaseId: FF-80-00-00)"
        new = "EnOcean Gateway - fam14 (Id: 1, BaseId: FF-80-00-00)"
        self.assertEqual(config_helpers.normalize_gateway_description(old), new)
        self.assertEqual(config_helpers.normalize_gateway_description(new), new)


if __name__ == "__main__":
    unittest.main()
