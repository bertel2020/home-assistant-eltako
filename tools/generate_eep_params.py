"""Generate constructor documentation using the manifest-pinned library.

Run from the repository root after installing requirements.txt:
    python -m tools.generate_eep_params
"""
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path

from eltakobus import eep

ROOT = Path(__file__).resolve().parents[1]
UNSUPPORTED = ('A5-09-0C', 'A5-38-08')


def render_eep_params():
    manifest = json.loads((ROOT / 'custom_components/eltako/manifest.json').read_text())
    requirement = next(r for r in manifest['requirements'] if r.startswith('eltako14bus @ '))
    url = requirement.split(' @ ', 1)[1]
    direct = json.loads(metadata.distribution('eltako14bus').read_text('direct_url.json'))
    if direct['url'] != url:
        raise RuntimeError('Install the manifest-pinned eltako14bus before generating documentation')
    lines = [
        '# EEP parameters for the Send Message service', '',
        f'Generated from the [manifest-pinned bertel2020 library]({url})',
        f'(package version {metadata.version("eltako14bus")}).',
        'Regenerate with `python -m tools.generate_eep_params` after installing `requirements.txt`.', '',
        'These are constructor parameter names, not a guarantee that every profile can be sent.',
        'The service fills omitted parameters with **0**, even when the constructor has another default.',
        'Supply all values needed by your device. This service uses `encode_message`,',
        'whereas the custom climate controller uses its own `encode_message2` path.', '',
        '## Profiles excluded by the existing service documentation', '',
        *[f'- `{name}`' for name in UNSUPPORTED], '',
        'A5-09-04 receives CO2 correctly, but its current outgoing encoder references',
        '`learn_button`, which its constructor does not provide. Do not use that profile',
        'for sending until separately corrected and validated.', '',
        'A5-10-06 currently expects Python enum objects for `mode` and `priority`.',
        'The service does not convert JSON/YAML values into those enums, so ordinary',
        'service calls for this profile are not supported. This is separate from',
        'the custom climate controller, whose existing send path is unchanged.', '',
        '## Constructor parameters', '',
    ]
    profiles = {cls.eep_string: cls for cls in vars(eep).values()
                if isinstance(cls, type) and issubclass(cls, eep.EEP) and hasattr(cls, 'eep_string')}
    for name, cls in sorted(profiles.items()):
        if name in UNSUPPORTED:
            continue
        params = sorted(p.name for p in inspect.signature(cls.__init__).parameters.values()
                        if p.name != 'self' and p.kind == p.POSITIONAL_OR_KEYWORD)
        lines.append(f'- `{name}`: {", ".join(params)}')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    (ROOT / 'docs/service-send-message/eep-params.md').write_text(render_eep_params())
