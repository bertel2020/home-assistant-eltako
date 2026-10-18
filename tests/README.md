# Focused maintenance checks

Install the repository's `requirements.txt` in Python 3.14 (HA 2026.10.2).
Run these modules separately: older tests patch global platform and library APIs.

```sh
python -m unittest discover -s tests -p test_dependencies.py
python -m unittest discover -s tests -p test_metadata.py
python -m unittest discover -s tests -p test_lifecycle.py
python -m unittest discover -s tests -p test_restore_regressions.py
python -m unittest discover -s tests -p test_gateway_diagnostics.py
python -m unittest discover -s tests -p test_service_contract.py
```

These verify dependency provenance, import/conversion behavior, unload cleanup,
saved-state recovery, stable gateway diagnostic identities and service telegrams.
They do not use connected hardware or send messages to a real bus.

Regenerate the parameter reference explicitly with
`python -m tools.generate_eep_params`. Documentation checks compare generated
text without writing repository files.

The legacy suite is not entirely green: some constructor mocks are outdated and
some synchronous tests assume an implicit asyncio event loop, which Python 3.14
no longer creates. Do not interpret these focused checks as a full-suite pass.
The service contract tests also document the existing A5-10-06 numeric-enum
limitation; this maintenance work does not change encoding or add enum conversion.
