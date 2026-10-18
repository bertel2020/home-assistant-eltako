# Dependencies and installation verification

The runtime source of truth is `custom_components/eltako/manifest.json`.
Home Assistant installs those requirements automatically when loading the
integration. The repository's `requirements.txt` includes exactly the same
runtime requirements, plus the development host and legacy discovery tools.

## Verified sources

| Package | Source |
| --- | --- |
| eltako14bus 1.2 | bertel2020/eltako14bus, commit `76d0dba36311bbd7c2e2813133eaf4ca341d7ca1` |
| enocean 0.60.1 | bertel2020/enocean, commit `7956cce9365ae13dc057ba8bb09e2934fe5a1b2f` |
| esp2-gateway-adapter 0.2.21+bertel.1 | bertel2020/esp2_gateway_adapter, commit `7c8d6fccd2be057a1264b533a84ed140ff855569` |

All three owned libraries are requested using immutable HTTPS commit archives.
Installation does not require a Git executable, SSH credentials, or copying
Python files manually. `direct_url.json` records the actual archive source;
the tests verify it, rather than trusting a version number shared by forks.

The enocean fork differs from the previous production package in three files
(EEP database, parser error handling, and diagnostics). This is an intentional
source change. It still reports version 0.60.1, so checking only that version
cannot prove that the correct fork is installed.

## Previously hidden prerequisites

eltako14bus imports its serial, CoAP, and device modules from `__init__.py`.
Those modules require pyserial, pyserial-asyncio, aiocoap, and PyYAML, but its
setup.py has no mandatory `install_requires`. Extras alone do not reflect
the unconditional imports. The integration now explicitly supplies those
requirements. Avoid enabling its old `coap` extra: it pins aiocoap to 0.4a1.

The adapter also declares several of these dependencies, but relying only on
that indirect path concealed the library's packaging defect. A standalone
installation of the eltako14bus repository still needs a packaging correction
in that repository. No library repository was modified by this change.

enocean declares beautifulsoup4, enum-compat and pyserial. The adapter declares
enocean, eltako14bus, pyserial, pyserial-asyncio, aiocoap and zeroconf. The direct
fork requirements satisfy their version ranges in the tested environment.
Home Assistant owns its own core dependencies such as voluptuous. Native UTC
is used in the gateway so it no longer directly requires pytz.

## Verified environment and tests

Verified on a fresh macOS ARM64 virtual environment using Python 3.14.6 and
Home Assistant 2026.10.2, including that release's package_constraints.txt.
The test environment is separate from the production HA installation.
PyYAML 6.0.3 matches that release's core constraint. Compatibility with other
HA versions or platforms has not been established by these checks.

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

## Adapter correction and validation

The pinned adapter fork version `0.2.21+bertel.1` supplies all seven ERP1
optional bytes for RPS, 1BS and 4BS and preserves the outgoing marker.
This fixes the RPS parser error and the loss of the outgoing flag in 0.2.21.
Its package declaration and repository URL are corrected as well.

The adapter tests pass six byte-exact software roundtrips (three telegram
types, each incoming and outgoing) plus an unsupported-message check.
The integration includes a passing RPS parser regression test. Hardware
communication and acceptance by physical gateways were not tested.

pyserial-asyncio is marked deprecated by HA 2026.10.2 for direct integration
requirements, with removal announced for 2027.2. The existing library and
adapter import it, so a future migration must be coordinated across those
packages rather than changing only the manifest.
