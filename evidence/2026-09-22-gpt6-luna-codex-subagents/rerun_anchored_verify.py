#!/usr/bin/env python3
"""Post-freeze verifier anchored to the public pre-label commitment."""
import argparse
import importlib.util
from pathlib import Path

SCORER = Path(__file__).with_name('rerun_scoring.py')
_spec = importlib.util.spec_from_file_location('luna_rerun_scoring', SCORER)
scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scoring)

ANCHOR_COMMIT = '11e84b1da82250f12bed54927230209236f50cdc'
RAW_COMMITMENT_SHA256 = 'bb149ea4a58101e48e6492fab3cfc6f1f0dccd9601ec24c69a00716b8b7f6d2b'


def verify(results_path, provenance_path, freeze_path, commitment_path, output_path):
    """Require the published pre-label anchor, then delegate all frozen checks."""
    scoring.h.require(scoring.h.sha256_file(commitment_path) == RAW_COMMITMENT_SHA256,
                      'raw commitment differs from public pre-label anchor')
    return scoring.verify(results_path, provenance_path, freeze_path, commitment_path, output_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('results', 'provenance', 'freeze', 'commitment', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(args.results, args.provenance, args.freeze, args.commitment, args.output)
    print('Completed anchored verification at ' + ANCHOR_COMMIT)


if __name__ == '__main__':
    main()
