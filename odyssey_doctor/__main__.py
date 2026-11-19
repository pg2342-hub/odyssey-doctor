"""CLI: python -m odyssey_doctor <path> [--json]"""
import argparse
import json
import sys

from .checks import RULES, scan


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="odyssey-doctor", description="Static checks for apps built on the Odyssey API.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="print machine-readable output")
    args = ap.parse_args(argv)
    rep = scan(args.path)
    if args.json:
        print(json.dumps({
            "root": rep.root, "uses_js_sdk": rep.uses_js_sdk, "uses_py_sdk": rep.uses_py_sdk,
            "files_scanned": rep.files_scanned,
            "findings": [{"rule": f.rule, "title": f.title, "path": f.path, "line": f.line, "detail": f.detail} for f in rep.findings],
        }, indent=2))
        return 1 if rep.findings else 0
    if not rep.uses_sdk:
        print("No Odyssey SDK usage found.")
        return 0
    if not rep.findings:
        print("No issues found.")
        return 0
    for f in sorted(rep.findings, key=lambda x: (x.rule, x.path, x.line)):
        extra = f" ({f.detail})" if f.detail else ""
        print(f"{f.rule}  {f.path}:{f.line}  {f.title}{extra}")
        print(f"       fix: {RULES[f.rule][1]}")
    print(f"\n{len(rep.findings)} issue(s) in {len(rep.rules_hit())} rule(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
