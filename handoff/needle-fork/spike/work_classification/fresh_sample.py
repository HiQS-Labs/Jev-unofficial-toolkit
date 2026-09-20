"""Draw the GH-69 fresh sample: public HiQS-Labs issues/PRs unseen by the #31 round.

Keyword-blind, deterministic (seeded), one repo capped so the sample is not one repo's view of
the world. Writes quiz.jsonl (the rows the annotators and Jev see), manifest.json (pool counts,
seed, exclusions, snapshot time, sha256 of quiz.jsonl) and QUIZ.md (instructions + rows).

    python spike/work_classification/fresh_sample.py --out TESTS-RESULTS/2026-09-19-jev-fresh-sample
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

ORG = "HiQS-Labs"
SINCE = "2026-09-10T00:00:00Z"   # after the #31 collection (input freeze 47baf02, 2026-09-10)
SEED = 20260919
N = 100
CAP = {"HiQS-Labs/XYZ-forge": 55}
DESC_LIMIT = 1800                # the #31 description boundary
# This project's own artifacts about Jev: excluded so the experiment does not grade itself.
EXCLUDE = {("HiQS-Labs/Needle-fork", "issue", 67), ("HiQS-Labs/Needle-fork", "issue", 69),
           ("HiQS-Labs/XYZ-forge", "issue", 709), ("HiQS-Labs/XYZ-forge", "issue", 712),
           ("HiQS-Labs/XYZ-forge", "pr", 714)}


def gh(args):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        if "has disabled issues" in proc.stderr:   # a fork with issues off contributes only PRs
            return []
        raise RuntimeError(f"gh {' '.join(args)}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout or "[]")


def public_repos():
    rows = gh(["repo", "list", ORG, "--limit", "100", "--json", "name,visibility,isArchived"])
    return sorted(f"{ORG}/{r['name']}" for r in rows if r["visibility"] == "PUBLIC" and not r["isArchived"])


def pool_for(repo):
    out = []
    for kind, verb in (("issue", "issue"), ("pr", "pr")):
        rows = gh([verb, "list", "--repo", repo, "--state", "all", "--limit", "500",
                   "--search", f"created:>={SINCE[:10]}", "--json", "number,title,body,createdAt,url"])
        for r in rows:
            if r["createdAt"] < SINCE or (repo, kind, r["number"]) in EXCLUDE:
                continue
            body = (r.get("body") or "").strip()
            out.append({"repo": repo, "kind": kind, "number": r["number"], "url": r["url"],
                        "created_at": r["createdAt"], "title": r["title"].strip(),
                        "description": body[:DESC_LIMIT], "description_truncated": len(body) > DESC_LIMIT})
    return out


def draw(pool, n=N, seed=SEED, cap=CAP):
    rng = random.Random(seed)
    by_repo = {}
    for r in sorted(pool, key=lambda r: (r["repo"], r["kind"], r["number"])):
        by_repo.setdefault(r["repo"], []).append(r)
    picked = []
    for repo, rows in sorted(by_repo.items()):
        rng.shuffle(rows)
        picked.extend(rows[:cap.get(repo, len(rows))])
    rng.shuffle(picked)
    return picked[:n]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if (out / "quiz.jsonl").exists():
        raise SystemExit(f"{out}/quiz.jsonl exists; the sample is frozen")
    snapshot = dt.datetime.now(dt.timezone.utc).isoformat()
    repos = public_repos()
    pool = []
    for repo in repos:
        pool.extend(pool_for(repo))
    sample = draw(pool)
    if len(sample) < N:
        raise SystemExit(f"pool too small: {len(sample)} < {N}")
    for i, r in enumerate(sample, 1):
        r["id"] = f"fresh-{i:03d}"
    out.mkdir(parents=True, exist_ok=True)
    quiz = "".join(json.dumps({k: r[k] for k in ("id", "repo", "kind", "number", "url", "created_at", "title", "description", "description_truncated")}, ensure_ascii=False) + "\n" for r in sample)
    (out / "quiz.jsonl").write_text(quiz)
    manifest = {"snapshot_utc": snapshot, "since": SINCE, "seed": SEED, "n": N, "cap": CAP,
                "description_limit": DESC_LIMIT, "excluded": sorted(list(x) for x in EXCLUDE),
                "public_repos": repos,
                "pool_by_repo": {repo: sum(1 for r in pool if r["repo"] == repo) for repo in repos},
                "sample_by_repo": {repo: sum(1 for r in sample if r["repo"] == repo) for repo in sorted({r["repo"] for r in sample})},
                "sample_by_kind": {k: sum(1 for r in sample if r["kind"] == k) for k in ("issue", "pr")},
                "quiz_sha256": hashlib.sha256(quiz.encode("utf-8")).hexdigest(),
                "commitments": {}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: manifest[k] for k in ("pool_by_repo", "sample_by_repo", "sample_by_kind", "quiz_sha256")}, indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
