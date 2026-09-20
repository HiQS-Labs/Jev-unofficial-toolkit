# Work-classification experiments

Offline research code for the HiQS work-purpose / component-area task (Needle #29 taxonomy,
#31 calibrated round). Not part of the installed `needle` runtime and not a serving model.

- `jev_zero_shot.py` — GH-67: TypeSafe Jev `jev-1.13.0` zero-shot on the frozen #31 40-record
  holdout, scored with the #547 metric definitions. Criteria are frozen by commit; the script
  refuses to run if the local cache differs from the pinned hashes or a record's repo is not
  `PUBLIC`. Protocol and result: `PROJECT/2-WORKING/GH-67-JEV-PURPOSE-ZERO-SHOT.md`,
  `TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/`.

```sh
python spike/work_classification/jev_zero_shot.py --dry-run
python spike/work_classification/jev_zero_shot.py --key-file <secret> --out TESTS-RESULTS/<date>-jev-purpose-zero-shot
```

Requires the operator's local `~/.cache/xyz-modernbert-calibrated/` snapshot and an authenticated `gh`.
