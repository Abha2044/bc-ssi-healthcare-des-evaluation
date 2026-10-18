"""Load the component inventory from models/components/*.json.

One file per component, so a reviewer can open C6.json and read only C6.
_conventions.json holds the shared header (source, rules) that used to sit at
the top of baseline_components.json. Nothing else changed.
"""
import json
from pathlib import Path


def _read(path):
    def unique(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError(f'{path}: duplicate JSON key {key}')
            seen[key] = value
        return seen
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def load_conventions(models_dir):
    return _read(Path(models_dir) / 'models' / '_conventions.json'
                 if (Path(models_dir) / 'models').is_dir()
                 else Path(models_dir) / '_conventions.json')


def load_components(models_dir):
    """Return the component list, in the order _order.json declares."""
    folder = Path(models_dir) / 'components'
    order = _read(folder / '_order.json')['components']
    on_disk = sorted(p.stem for p in folder.glob('*.json') if not p.stem.startswith('_'))
    if sorted(order) != on_disk:
        raise ValueError(
            f'components/_order.json lists {sorted(order)} but the folder holds {on_disk}. '
            'Add or remove the file, and update _order.json to match.')
    return [_read(folder / f'{cid}.json') for cid in order]
