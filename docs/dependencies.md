# Dependencies and installation verification

The runtime source of truth is `custom_components/eltako/manifest.json`.
Home Assistant installs those requirements automatically when loading the
integration. The repository's `requirements.txt` contains exactly the same
runtime requirements, plus the development host.
`tests/test_dependencies.py` checks that both lists stay in sync.

## Runtime requirements (manifest.json)

| Package | Pin | Used by | Purpose |
| --- | --- | --- | --- |
| eltako14bus 1.2.2 | fork, commit `f3c16278312ade28e5972bea5f5ff425469f9bbe` | integration (`eltakobus`) | Eltako RS485 bus, ESP2 telegrams, EEP definitions |
| enocean 0.60.1 | fork, commit `7956cce9365ae13dc057ba8bb09e2934fe5a1b2f` | adapter (`enocean`) | ESP3 packets and EEP database |
| esp2-gateway-adapter 0.2.21+bertel.1 | fork, commit `13358d198e069ea0fe21a2354442b475cdd79b22` | integration | ESP3 serial/TCP gateways presented as ESP2 |
| pyserial 3.5 | exact | integration (`gateway.py`), eltako14bus, adapter | serial ports |
| pyserial-asyncio-fast 0.16 | exact | eltako14bus (`serial_asyncio_fast`) | async serial I/O; replaces pyserial-asyncio |
| aiocoap 0.4.17 | exact | eltako14bus (optional, imported lazily) | CoAP module of the library; kept pinned so its optional CoAP support stays on a tested version |
| PyYAML 6.0.3 | exact | eltako14bus (`device.py`), tests | YAML; matches the HA 2026.10.2 core constraint |

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
| eltako14bus, enocean, pyserial, aiocoap | esp2-gateway-adapter | also requested directly, see above |
| voluptuous and other HA core packages | Home Assistant | owned by HA, never pinned by the integration |

`pytz` is no longer required: the gateway uses native UTC (`datetime.UTC`).

## Previously hidden prerequisites

Older eltako14bus commits imported their serial, CoAP, and device modules from
`__init__.py` without declaring pyserial, pyserial-asyncio, aiocoap, and PyYAML
in `install_requires`. Since 1.2.1 the library declares pyserial, PyYAML and the
serial transport as mandatory requirements and imports aiocoap lazily (extra
`coap`); since 1.2.2 the serial transport is `pyserial-asyncio-fast`. The
manifest still pins these packages explicitly so the tested versions are
installed. Avoid enabling the library's old `coap` extra: it pins aiocoap to
0.4a1.

## Development and test requirements (requirements.txt only)

These are not part of the manifest and are never installed by Home Assistant.

| Package | Pin | Purpose |
| --- | --- | --- |
| homeassistant 2026.10.2 | exact | development host matching the verified production release (Python 3.14) |
| packaging | transitive via HA | `tests/test_dependencies.py`, `tests/test_metadata.py` |
| pytest | not in `requirements.txt` | installed separately by the CI workflow; the suite also runs with `unittest` |

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
example `ModuleNotFoundError: serial_asyncio_fast`); the dependency tests skip their
runtime checks if Home Assistant is missing.

## CI

`.github/workflows/test_on_push.yml` installs `requirements.txt` on Python 3.14,
runs `pip check`, then the dependency and metadata tests separately. The full
legacy suite runs afterwards with `continue-on-error`, so it does not block the
build.

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

- **pyserial-asyncio:** Home Assistant's developer blog (2026-01-05) announces
  that installing it is blocked from HA 2026.7, with `pyserial-asyncio-fast`
  (module `serial_asyncio_fast`) as drop-in replacement; the 2026-04-27 post
  recommends `serialx` for pyserial and both asyncio variants. Only eltako14bus
  imports it (`eltakobus/serial.py`); the adapter merely declared it.
  Done: eltako14bus 1.2.2 uses `pyserial-asyncio-fast`, the adapter no longer
  declares the dependency, and the manifest pins the new commits and
  `pyserial-asyncio-fast==0.16`. The pins sit on the `vld-support` line of both
  libraries (branches `serial-asyncio-fast-vld`, `drop-pyserial-asyncio-vld`).
  `serialx` remains an open follow-up: `pyserial` stays installed through
  enocean, whose `communicators` package imports `serial`.
- **Fork maintenance:** the three forks must be re-pinned by commit hash after
  every change; a branch or tag reference would break the immutability
  guarantee that the tests assert.
- **Upstream documentation:** `README.md` still links the upstream projects
  (grimmpp/eltako14bus, grimmpp/esp2_gateway_adapter, kipe/enocean), not the
  pinned forks.
