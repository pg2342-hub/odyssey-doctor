"""Clone the public projects in projects.csv at their pinned commits and run odyssey-doctor on each.

Usage: python corpus/run_corpus.py [workdir]
Prints a per-rule count across distinct projects (repos in the same group count once).
Findings are reported in aggregate. OD002 (literal keys) is skipped for public projects.
"""
import csv
import os
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from odyssey_doctor.checks import RULES, scan  # noqa: E402


def fetch(repo, commit, dest, paths=""):
    """Clone at a pinned commit. `paths` (space-separated) limits large repos to the Odyssey code."""
    if not os.path.isdir(os.path.join(dest, ".git")):
        if paths:
            subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout",
                            f"https://github.com/{repo}.git", dest], check=True)
            subprocess.run(["git", "-C", dest, "sparse-checkout", "set", *paths.split()], check=True)
        else:
            subprocess.run(["git", "clone", "-q", f"https://github.com/{repo}.git", dest], check=True)
    subprocess.run(["git", "-C", dest, "checkout", "-q", commit], check=True)


def main():
    work = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, ".work")
    os.makedirs(work, exist_ok=True)
    groups = defaultdict(set)
    uses = {}
    with open(os.path.join(HERE, "projects.csv")) as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        dest = os.path.join(work, row["repo"].replace("/", "_"))
        fetch(row["repo"], row["commit"], dest, row.get("paths") or "")
        rep = scan(dest)
        groups[row["group"]] |= rep.rules_hit()
        uses[row["group"]] = uses.get(row["group"], False) or rep.uses_sdk
    n = sum(1 for g in groups if uses[g])
    print(f"{len(rows)} repositories, {n} distinct projects using the SDK\n")
    print("| Rule | Check | Projects |\n|---|---|---|")
    for rule, (title, _) in RULES.items():
        if rule == "OD002":
            continue  # literal keys in other people's public repos are not reported here
        k = sum(1 for g, r in groups.items() if uses[g] and rule in r)
        print(f"| {rule} | {title} | {k} of {n} |")


if __name__ == "__main__":
    main()
