import unittest
from unittest.mock import MagicMock, patch

import serial

from custom_components.eltako import gateway


class TestValidatePath(unittest.TestCase):

    def test_valid_path_closes_the_probe_connection(self):
        port = MagicMock()
        with patch.object(gateway.serial, "serial_for_url", return_value=port):
            self.assertTrue(gateway.validate_path("/dev/ttyUSB0", 57600))
        port.close.assert_called_once_with()

    def test_serial_exception_means_invalid(self):
        with patch.object(gateway.serial, "serial_for_url", side_effect=serial.SerialException("busy")):
            self.assertFalse(gateway.validate_path("/dev/ttyUSB0", 57600))

    def test_native_os_errors_mean_invalid(self):
        # Libraries such as serialx raise native exceptions instead of SerialException.
        for error in (FileNotFoundError("no such device"), PermissionError("denied"), TimeoutError("timeout")):
            with self.subTest(error=type(error).__name__):
                with patch.object(gateway.serial, "serial_for_url", side_effect=error):
                    self.assertFalse(gateway.validate_path("/dev/missing", 57600))


if __name__ == "__main__":
    unittest.main()
