# Portions adapted from HiQS-Labs/Needle-fork at f7c7047, Apache-2.0.
# Attribution and modification notice: ../NOTICE; license: ../licenses/Apache-2.0.txt.
"""Freeze, blind commitments, visibility policy, and the sole results writer."""
import json
import subprocess
from pathlib import Path
from .client import canonical, sha256

DENIED = {"title", "description", "stderr", "stdout", "body"}
POLICY = {"allowed_owners": ["HiQS-Labs"], "denied_owners": ["BinoidCBD", "LTVera"],
          "denied_repos": []}
FROZEN_QUESTIONS = {'work_purpose_v3': '21094cd4f260f09986f70626d8991be8e9650c103bb107d3740d57219aed2821', 'ate_triage_v1': '65e8dc9a32bf163b2ebefe183e3c50ed532f3f3b0a5ae6371a7eb43f884aeaa7'}
FROZEN_FIXTURES = {'purpose-40': {'confusions.json': '13c00c5fee29eec83cfc453cf80fc8ff81e8fe3607b25faa245d2b0a7f929412', 'expected.json': '68d9918c9c5e551f6366f8c143b49e55f09237c89bd5cb36421afc431691d2ea', 'historical-hashes.json': '6b20d791fb8fc600bff51bc52caf390b12c830b6b531bd2609a557d1c6b22d93', 'manifest.json': '265209b4f97aac41ed81d39a4e59cca52ac94eea94f5a8797b7854384eb7dd5a', 'metadata.json': '3d24e88a1507e3aee26e6e38b4ac65f734f81b0b6b030af5d4932fe89795dada', 'records.json': '221a5e6bddaaf69b4e67c3fd0cc2b650dfc680c3464ab60cf5bf4134e569e8ee', 'responses.json': '30e3377dd92fccb3329d03c5f7604791b0e160c6bcf7f5dfa7556c33731be1c8'}, 'fresh-100': {'annotators.json': '06d856924f41cb4940176f6e5b51fca8fb8b13972a17c6ecfa2fad55fb4dbdff', 'expected.json': '304ae72dccc63fdf7ab286c58767882fdf48c4aa940623159d3368c33aee4c90', 'historical-hashes.json': 'a50e422b639f61849a84d23f3287247bb27fb46dcb9b2a5b33c501ffba5e7301', 'labels.json': 'e9e39d5ffe76f74b35ed912434ecafe5e0f45f4233bec169f90a05a369459a59', 'manifest.json': '103dfc40ae50ff0ca67259424a3ba6a1870cb24e492feb30bdc1d52a88e6d9b0', 'metadata.json': 'ff4159b18fc498447d04d04a8d008b6cb655804cf9287a034f21c47bdc0ac6a4', 'records.json': '7abec9f1e0880c3917db2138e31d21b7be20823bdd2043d65d6eb6bc86acb70a', 'responses.json': 'bf3de130985b00e77f57b27959ec5cfd23fcde00224fdeb3e3ea3bb95c05e425'}, 'ate-benchmark': {'historical-hashes.json': '8d1729a88db101df56013a5f0ebde06396e8bf98511196e9d2dbbfe07463fbb5', 'historical-summary.json': 'ee5484b7710767e18dced8239a8f41bc680f6b70790a4c38a0814da2cee9eba8', 'labels.json': '58bf51e28275153fd72d7736d69947acdad1a617f214c3f452867aeddaeb8d74', 'manifest.json': 'f9a5a5bb13198feecb1aaf84089281963f08b0c85e168578b56aaa9e5c41a693', 'records.json': 'e983f3f16b688344ff231cafe901553fdf009cedc85edfe19c2851c003e727d8', 'reference.json': '0cd404acebd6c11521ac52d2b1082da764be76af56cab59e9f0125703f35acec', 'responses.json': '8e4c9185c2e2acb83cceef9c29504a9c3cc253e339dad244f7268df8d4236ac6'}}


def verify_freeze(directory, expected):
    if not expected:
        raise ValueError("empty freeze")
    seen = {name: sha256((Path(directory) / name).read_bytes()) for name in expected}
    if seen != expected:
        raise ValueError("freeze mismatch")
    return seen


def load_questions(name):
    directory = Path(__file__).parent / "questions"
    if name not in FROZEN_QUESTIONS:
        raise ValueError("unknown frozen question set")
    expected = FROZEN_QUESTIONS[name]
    verify_freeze(directory, {name + ".json": expected})
    if (directory / (name + ".sha256")).read_text().strip() != expected:
        raise ValueError("question sidecar mismatch")
    return json.loads((directory / (name + ".json")).read_text())


def commit(labels_file):
    return {"labels_sha256": sha256(Path(labels_file).read_bytes())}


def verify(labels_file, manifest):
    if commit(labels_file) != {"labels_sha256": manifest["labels_sha256"]}:
        raise ValueError("annotation commitment mismatch")
    return True


def repo_visibility(repos, policy=POLICY, runner=None):
    runner = runner or subprocess.run
    result = {}
    for repo in sorted(set(repos)):
        owner, sep, name = repo.partition("/")
        allowed = {x.casefold() for x in policy["allowed_owners"]}
        denied = {x.casefold() for x in policy["denied_owners"]}
        if not sep or not name or owner.casefold() not in allowed or owner.casefold() in denied or repo in policy["denied_repos"]:
            result[repo] = "DENIED"
            continue
        proc = runner(["gh", "repo", "view", repo, "--json", "visibility", "-q", ".visibility"],
                      capture_output=True, text=True)
        result[repo] = "PUBLIC" if proc.returncode == 0 and proc.stdout.strip() == "PUBLIC" else "DENIED"
    return result


def safe_results(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or key.casefold() in DENIED:
                raise ValueError("forbidden results field")
            safe_results(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            safe_results(child)
    return value


def write_results(path, value):
    """Validate fully before creating the file; never overwrite a prior result."""
    safe_results(value)
    raw = json.dumps(value, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(raw)
