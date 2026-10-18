# Dependencies and installation verification

The runtime source of truth is `custom_components/eltako/manifest.json`.
Home Assistant installs those requirements automatically when loading the
integration. The repository's `requirements.txt` contains exactly the same
runtime requirements, plus the development host and legacy discovery tools.
`tests/test_dependencies.py` checks that both lists stay in sync.

## Runtime requirements (manifest.json)

| Package | Pin | Used by | Purpose |
| --- | --- | --- | --- |
| eltako14bus 1.2 | fork, commit `6cb99f7fbee3391e348b9d3f1cffee61b7c816d8` | integration (`eltakobus`) | Eltako RS485 bus, ESP2 telegrams, EEP definitions |
| enocean 0.60.1 | fork, commit `7956cce9365ae13dc057ba8bb09e2934fe5a1b2f` | adapter (`enocean`) | ESP3 packets and EEP database |
| esp2-gateway-adapter 0.2.21+bertel.1 | fork, commit `450dcbe4567958f7e5acc617b930276b1810331a` | integration | ESP3 serial/TCP gateways presented as ESP2 |
| StrEnum 0.4.15 | exact | integration (`const.py`, `from strenum import StrEnum`) | string enums for gateway device types |
| pyserial 3.5 | exact | integration (`gateway.py`), eltako14bus, adapter | serial ports |
| pyserial-asyncio 0.6 | exact | eltako14bus, adapter | async serial I/O |
| aiocoap 0.4.17 | exact | eltako14bus (unconditional import) | CoAP module of the library |
| PyYAML 6.0.3 | exact | eltako14bus (unconditional import), tests | YAML; matches the HA 2026.10.2 core constraint |

The three forks (all owned by bertel2020) are requested as immutable HTTPS
commit archives. Installation does not require a Git executable, SSH
credentials, or copying Python files manually. `direct_url.json` in each
installed distribution records the actual archive source; the tests verify it
rather than trusting a version number, because the forks share the version
numbers of their upstream projects.

The enocean fork differs from the previous production package in three files
(EEP database, parser error handling, and diagnostics). This is an intentional
source change. It still reports version 0.60.1, so checking only that version
cannot prove that the correct fork is installed.

## Transitive dependencies

Not listed in the manifest; pulled in by the libraries above.

| Package | Declared by | Note |
| --- | --- | --- |
| beautifulsoup4, enum-compat | enocean | satisfied in the tested environment |
| zeroconf | esp2-gateway-adapter | provided by Home Assistant core in the tested environment; not pinned here |
| eltako14bus, enocean, pyserial, pyserial-asyncio, aiocoap | esp2-gateway-adapter | also requested directly, see above |
| voluptuous and other HA core packages | Home Assistant | owned by HA, never pinned by the integration |

`pytz` is no longer required: the gateway uses native UTC (`datetime.UTC`).

## Previously hidden prerequisites

eltako14bus imports its serial, CoAP, and device modules from `__init__.py`.
Those modules require pyserial, pyserial-asyncio, aiocoap, and PyYAML, but its
setup.py has no mandatory `install_requires`. Extras alone do not reflect
the unconditional imports. The integration therefore supplies those
requirements explicitly. Avoid enabling the library's old `coap` extra: it
pins aiocoap to 0.4a1.

The adapter also declares several of these dependencies, but relying only on
that indirect path concealed the library's packaging defect. A standalone
installation of the eltako14bus repository still needs a packaging correction
in that repository. No library repository was modified by this change.

## Development and test requirements (requirements.txt only)

These are not part of the manifest and are never installed by Home Assistant.

| Package | Pin | Purpose |
| --- | --- | --- |
| homeassistant 2026.10.2 | exact | development host matching the verified production release (Python 3.14) |
| termcolor | unpinned | legacy `eltakodevice_discovery` tools only |
| packaging | transitive via HA | `tests/test_dependencies.py`, `tests/test_metadata.py` |
| pytest | not in `requirements.txt` | installed separately by the CI workflow; the suite also runs with `unittest` |

The legacy discovery tools (`eltakodevice_discovery/`) additionally need
`tkinter` (`dd_gui.py`), which is a system package and cannot be installed by
pip. They are not used by the integration at runtime.

## Verified environment and tests

Verified on a fresh macOS ARM64 virtual environment using Python 3.14.6 and
Home Assistant 2026.10.2, including that release's package_constraints.txt.
The test environment is separate from the production HA installation.
Compatibility with other HA versions, Python versions or platforms has not
been established by these checks.

For local development with Python 3.14:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -p test_dependencies.py -v
.venv/bin/python -m unittest discover -s tests -p test_metadata.py -v
```

These checks verify source provenance, version constraints, imports of every
enabled platform and both transport backends, a temperature EEP decode, and
ESP2/ESP3 conversion preserving payload, address and status. The 4BS test also
checks byte-exact roundtrip. Run these tests separately: the legacy suite
patches library functions globally during collection.

Without the requirements installed the suite fails during collection (for
example `ModuleNotFoundError: serial_asyncio`); the dependency tests skip their
runtime checks if Home Assistant is missing.

## CI

`.github/workflows/test_on_push.yml` installs `requirements.txt` on
`python-version: '3.x'` and runs `python -m unittest discover tests`. This is
not pinned to the verified Python 3.14 and does not run the dependency tests
separately as described above, so a green CI run is weaker evidence than the
local procedure.

## Adapter correction and validation

The pinned adapter fork version `0.2.21+bertel.1` supplies all seven ERP1
optional bytes for RPS, 1BS and 4BS and preserves the outgoing marker.
This fixes the RPS parser error and the loss of the outgoing flag in 0.2.21.
Its package declaration and repository URL are corrected as well.

The adapter tests pass six byte-exact software roundtrips (three telegram
types, each incoming and outgoing) plus an unsupported-message check.
The integration includes a passing RPS parser regression test. Hardware
communication and acceptance by physical gateways were not tested.

## Known open points

- **pyserial-asyncio** is marked deprecated by HA 2026.10.2 for direct
  integration requirements, with removal announced for 2027.2. The library and
  adapter import it, so a migration must be coordinated across those packages
  rather than changing only the manifest.
- **Fork maintenance:** the three forks must be re-pinned by commit hash after
  every change; a branch or tag reference would break the immutability
  guarantee that the tests assert.
- **Upstream documentation:** `README.md` still links the upstream projects
  (grimmpp/eltako14bus, grimmpp/esp2_gateway_adapter, kipe/enocean), not the
  pinned forks.
