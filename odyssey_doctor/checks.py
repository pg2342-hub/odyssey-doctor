"""Static checks for projects that use the Odyssey JS or Python SDK.

Each check reads source text only. Nothing is executed and no network call is made.
Every rule cites the public Odyssey doc page or SDK behavior it is based on.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".html", ".vue", ".svelte"}
PY_EXT = {".py"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "venv", ".venv", "__pycache__", "coverage"}

JS_SDK = re.compile(r"""['"]@odysseyml/odyssey(?:/react)?['"]|esm\.sh/@odysseyml/odyssey""")
PY_SDK = re.compile(r"^\s*(from\s+odyssey(\.\w+)?\s+import\s+.*\bOdyssey\b|from\s+odyssey\s+import|import\s+odyssey\b)", re.M)
KEY_LITERAL = re.compile(r"\body_[A-Za-z0-9]{16,}\b")
PLACEHOLDER = re.compile(r"ody_(your|xxx|\.\.\.|api|key|example|placeholder|test|dummy|fake)", re.I)

RULES = {
    "OD001": ("API key reachable from browser code",
              "Browser bundles are public. Mint short-lived client credentials on a server (Client Credentials page)."),
    "OD002": ("Hard-coded API key in source",
              "A literal ody_ key in a repository can be copied by anyone who can read it. Load it from a server-side secret."),
    "OD003": ("No restart when a stream hits the 150-second limit",
              "Streams end with reason 'session_timeout' after 150 s. Handle onStreamError / on_stream_error and restart (Stream Duration Limits page)."),
    "OD004": ("Connection never released",
              "connect() without disconnect() leaves a session holding a concurrency slot until the server times it out (Session Management page)."),
    "OD005": ("No cleanup on page exit or component unmount",
              "Closed tabs and hot reloads leave dangling sessions. Disconnect in beforeunload / useEffect cleanup (Session Management page)."),
    "OD006": ("Usage limits not handled",
              "Monthly hours, concurrent streams and rate limits arrive as typed 429 errors (MonthlyLimitReachedError, ConcurrentLimitReachedError, RateLimitError). Catch them and tell the user."),
    "OD007": ("Wrong Python package",
              "PyPI's 'odyssey' is an unrelated project. Install the SDK from git+https://github.com/odysseyml/odyssey-python.git."),
    "OD009": ("Server route hands the raw API key to the browser",
              "An endpoint that returns the API key moves the leak, it does not stop it. Return client credentials from createClientCredentials() instead."),
    "OD008": ("Recovery path needs an API key the client does not have",
              "A client that joined with connectWithCredentials() cannot call connect() (it requires an API key). Fetch fresh credentials from your server instead."),
}


@dataclass
class Finding:
    rule: str
    path: str
    line: int
    detail: str = ""

    @property
    def title(self) -> str:
        return RULES[self.rule][0]


@dataclass
class Report:
    root: str
    uses_js_sdk: bool = False
    uses_py_sdk: bool = False
    files_scanned: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def uses_sdk(self) -> bool:
        return self.uses_js_sdk or self.uses_py_sdk

    def rules_hit(self) -> set[str]:
        return {f.rule for f in self.findings}


# Cleanup only counts when the page-exit or unmount handler releases the Odyssey session itself
# (not a socket or an IntersectionObserver that happens to have a disconnect() method).
def _release_pattern(whole_js: str) -> str:
    names = set(re.findall(r"(\w+)(?:\.current)?\s*=\s*new\s+Odyssey\s*\(", whole_js))
    names |= set(re.findall(r"(\w+)\s*=\s*useRef\s*<\s*Odyssey", whole_js))
    recv = r"(?:" + "|".join(sorted(re.escape(n) for n in names) + [r"\w*[Oo]dyssey\w*", r"\w*[Cc]lient\w*"]) + r")"
    # client.disconnect(), clientRef.current?.disconnect(), client.disconnect?.(), or a bare
    # disconnect() returned by the project's own wrapper hook
    release = (r"(?:" + recv + r"(?:\.current)?\??\.(?:disconnect|endStream|close)(?:\?\.)?\s*\("
               + r"|(?<![.\w])disconnect\s*\(\s*\))")
    return release


def _cleanup_re(whole_js: str):
    release = _release_pattern(whole_js)
    return re.compile(
        r"(beforeunload|pagehide|visibilitychange)['\"][^}]{0,300}?" + release
        + r"|onbeforeunload\s*=[^}]{0,300}?" + release
        + r"|return\s*\(\s*\)\s*=>\s*(\{[^}]{0,300}?|[^;\n]{0,120}?)" + release
        + r"|return\s+function\b[^}]*\{[^}]{0,300}?" + release)


def _iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _is_server_path(rel: str, text: str) -> bool:
    """Heuristic: code that only runs on a server."""
    rel_l = rel.replace("\\", "/").lower()
    if re.search(r"(^|/)(api|server|backend|functions|lambda|scripts?)(/|$)", rel_l):
        return True
    if re.search(r"(^|/)route\.(t|j)sx?$", rel_l) or rel_l.endswith((".server.ts", ".server.js")):
        return True
    if re.search(r"^\s*['\"]use server['\"]", text, re.M):
        return True
    if re.search(r"require\(['\"](express|fastify|koa)['\"]\)|from ['\"](express|fastify|koa|next/server)['\"]", text):
        return True
    return False


def _is_browser_code(rel: str, text: str) -> bool:
    rel_l = rel.lower()
    if rel_l.endswith((".html", ".vue", ".svelte")):
        return True
    if re.search(r"^\s*['\"]use client['\"]", text, re.M):
        return True
    if _is_server_path(rel, text):
        return False
    if rel_l.endswith((".jsx", ".tsx")):
        return True
    if re.search(r"\bdocument\.|\bwindow\.|srcObject|useEffect\(|useRef\(", text):
        return True
    return False


def _first_call(files, pattern):
    """Path and line of the first SDK call that can raise a usage error."""
    for rel, t in files:
        m = re.search(pattern, t)
        if m:
            return rel, _line_of(t, m.start())
    return files[0][0], 1


def scan(root: str) -> Report:
    rep = Report(root=os.path.abspath(root))
    js_files: list[tuple[str, str]] = []
    project_js: list[str] = []
    py_files: list[tuple[str, str]] = []
    dep_files: list[tuple[str, str]] = []
    for path in _iter_files(root):
        rel = os.path.relpath(path, root)
        ext = os.path.splitext(path)[1].lower()
        base = os.path.basename(path).lower()
        if base in {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "pipfile"} or base.startswith("requirements"):
            dep_files.append((rel, _read(path)))
        if ext in JS_EXT:
            t = _read(path)
            rep.files_scanned += 1
            project_js.append(t)
            if JS_SDK.search(t):
                rep.uses_js_sdk = True
                js_files.append((rel, t))
            elif KEY_LITERAL.search(t):
                js_files.append((rel, t))
        elif ext in PY_EXT:
            t = _read(path)
            rep.files_scanned += 1
            if PY_SDK.search(t) and (re.search(r"\bOdyssey\s*\(\s*api_key", t) or (
                    re.search(r"\w+\s*=\s*Odyssey\b", t) and re.search(r"api_key\s*=", t)
                    and re.search(r"\.(start_stream|simulate)\s*\(", t))):
                rep.uses_py_sdk = True
                py_files.append((rel, t))

    all_js = "\n".join(t for _, t in js_files)
    all_py = "\n".join(t for _, t in py_files)
    whole_js = "\n".join(project_js)  # cleanup often lives in a component that wraps the SDK

    # OD002: literal keys anywhere we looked (value is never printed)
    for rel, t in js_files + py_files:
        for m in KEY_LITERAL.finditer(t):
            if not PLACEHOLDER.match(m.group(0)):
                rep.findings.append(Finding("OD002", rel, _line_of(t, m.start()), "literal key (value not shown)"))

    # OD001: API key used in browser-side code, or exposed through a public env-var prefix
    for rel, t in js_files:
        hits = []
        for m in re.finditer(r"(NEXT_PUBLIC_|VITE_|REACT_APP_|EXPO_PUBLIC_|PUBLIC_)[A-Z_]*ODYSSEY[A-Z_]*", t):
            hits.append((_line_of(t, m.start()), m.group(0)))
        if _is_browser_code(rel, t):
            for m in re.finditer(r"new\s+Odyssey\s*\(\s*\{[^}]*apiKey|useOdyssey\s*\(\s*\{[^}]*apiKey", t, re.S):
                hits.append((_line_of(t, m.start()), ""))
        if hits:
            line, detail = hits[0]
            rep.findings.append(Finding("OD001", rel, line, detail))

    # OD009: a server route that returns the key itself
    for path in _iter_files(root):
        if os.path.splitext(path)[1].lower() not in JS_EXT:
            continue
        t = _read(path)
        if not re.search(r"ODYSSEY[A-Z_]*KEY", t):
            continue
        rel = os.path.relpath(path, root)
        m = re.search(r"json\(\s*\{\s*(apiKey|api_key|key)\s*[:,}]", t)
        if not m and _is_server_path(rel, t):
            # a server function that returns the key inside any object it hands back
            for k in re.finditer(r"\b(apiKey|api_key|key)\s*:\s*(process\.env\.)?\w*ODYSSEY\w*KEY\b", t):
                if not re.search(r"new\s+Odyssey\s*\(\s*\{[^}]*$", t[max(0, k.start() - 200):k.start()]):
                    m = k
                    break
        if m:
            rep.findings.append(Finding("OD009", rel, _line_of(t, m.start())))

    if rep.uses_js_sdk:
        streams = re.search(r"\.startStream\s*\(|startStream\s*\(", all_js)
        if streams and not re.search(r"session_timeout|duration_limit_reached", all_js):
            rel, t = next(((r, t) for r, t in js_files if "startStream" in t), js_files[0])
            rep.findings.append(Finding("OD003", rel, _line_of(t, t.find("startStream")) if "startStream" in t else 1))
        uses_hook = bool(re.search(r"\buseOdyssey\s*\(", all_js))  # the React hook disconnects on unmount
        if re.search(r"\.connect\s*\(|connectWithCredentials\s*\(", all_js) and not uses_hook:
            if not re.search(_release_pattern(whole_js), whole_js):
                rel, t = next(((r, t) for r, t in js_files if "connect" in t), js_files[0])
                rep.findings.append(Finding("OD004", rel, _line_of(t, t.find(".connect"))))
            elif not _cleanup_re(whole_js).search(whole_js):
                rel, t = next(((r, t) for r, t in js_files if "disconnect" in t), js_files[0])
                rep.findings.append(Finding("OD005", rel, _line_of(t, t.find("disconnect"))))
        if re.search(r"\.connect\s*\(|startStream\s*\(|simulate\s*\(", all_js) and not re.search(
                r"MonthlyLimitReached|ConcurrentLimitReached|RateLimitError|OdysseyUsageError|StreamDurationExceeded|CONCURRENT_LIMIT|MONTHLY_LIMIT|\b429\b", all_js):
            rel, line = _first_call(js_files, r"\.connect\s*\(|connectWithCredentials\s*\(|startStream\s*\(|simulate\s*\(")
            rep.findings.append(Finding("OD006", rel, line))
        if re.search(r"connectWithCredentials\s*\(", all_js) and re.search(r"session_timeout[\s\S]{0,400}\.connect\s*\(\s*\)", all_js):
            rel, t = next((r, t) for r, t in js_files if "connectWithCredentials" in t)
            rep.findings.append(Finding("OD008", rel, _line_of(t, t.find("connectWithCredentials"))))

    if rep.uses_py_sdk:
        if re.search(r"start_stream\s*\(", all_py) and not re.search(r"session_timeout|SESSION_TIMEOUT|duration_limit_reached", all_py):
            rel, t = next(((r, t) for r, t in py_files if "start_stream" in t), py_files[0])
            rep.findings.append(Finding("OD003", rel, _line_of(t, t.find("start_stream"))))
        if re.search(r"\.connect\s*\(", all_py) and not re.search(r"\.disconnect\s*\(", all_py):
            rel, t = py_files[0]
            rep.findings.append(Finding("OD004", rel, 1))
        if re.search(r"\.connect\s*\(|start_stream\s*\(|simulate\s*\(", all_py) and not re.search(
                r"MonthlyLimitReached|ConcurrentLimitReached|RateLimitError|OdysseyUsageError|StreamDurationExceeded", all_py):
            rel, line = _first_call(py_files, r"\.connect\s*\(|start_stream\s*\(|simulate\s*\(")
            rep.findings.append(Finding("OD006", rel, line))

    for rel, t in dep_files:
        if "odyssey-python" in t:
            continue
        base = os.path.basename(rel).lower()
        if base.startswith("requirements") or base == "pipfile":
            for m in re.finditer(r"^\s*odyssey\s*([=<>~!].*)?$", t, re.M):
                rep.findings.append(Finding("OD007", rel, _line_of(t, m.start())))
        else:
            for block in re.finditer(r"(dependencies|install_requires)\s*=\s*\[([^\]]*)\]", t):
                for m in re.finditer(r"['\"]odyssey\s*([=<>~!][^'\"]*)?['\"]", block.group(2)):
                    rep.findings.append(Finding("OD007", rel, _line_of(t, block.start(2) + m.start())))
    return rep
