# odyssey-doctor

Static checks for apps built on the [Odyssey API](https://documentation.api.odyssey.ml/) JavaScript and Python SDKs. It reads source files only: no API key, no network calls, nothing executed.

```bash
python -m odyssey_doctor path/to/your/app          # human-readable
python -m odyssey_doctor path/to/your/app --json   # for CI
```

Exit code is 1 when anything is found, so it can gate a CI step. Python 3.10+, no dependencies.

## Checks

| Rule | What it flags | Based on |
|---|---|---|
| OD001 | API key used in browser code, or exposed through a public env prefix (NEXT_PUBLIC_, VITE_, REACT_APP_, EXPO_PUBLIC_) | Client Credentials page |
| OD002 | A literal `ody_` key committed in source (the value is never printed) | Client Credentials page |
| OD003 | Streams started, but no restart when the stream ends with `session_timeout` at the 150-second limit | Stream Duration Limits page |
| OD004 | `connect()` with no `disconnect()` anywhere in the project | Session Management page |
| OD005 | `disconnect()` exists but no page-exit or unmount handler calls it on the Odyssey client | Session Management page |
| OD006 | None of the typed usage errors handled (MonthlyLimitReachedError, ConcurrentLimitReachedError, RateLimitError, StreamDurationExceededError, AccountSuspendedError) | SDK source (`throwIfUsageError`) |
| OD007 | `odyssey` from PyPI as a dependency (an unrelated project); the SDK installs from `git+https://github.com/odysseyml/odyssey-python.git` | Python SDK install docs |
| OD008 | A client that joined with `connectWithCredentials()` calls `connect()` to recover, which requires an API key it does not have | SDK source (`requireApiKey`) |
| OD009 | A server route or function that returns the raw API key (in a JSON response or any returned object) | Client Credentials page |

The React `useOdyssey` hook disconnects on unmount, so projects using it pass OD004 and OD005.

## How it did on public projects

`corpus/run_corpus.py` clones 20 public repositories that import the SDK (17 distinct projects) at pinned commits and runs every check. See [corpus/RESULTS.md](corpus/RESULTS.md). The OD001, OD003, OD005 and OD009 hits were each checked against the source: the 12 OD001 hits are all browser apps, the 12 OD003 hits are exactly the streaming projects, the single OD005 hit only disconnects on a mode switch, and the 4 OD009 hits return the key from a server function.

## Tests

```bash
python -m unittest discover -s tests -v
```

Fixtures cover a clean JavaScript app (server-minted credentials, timeout restart, usage errors, unmount cleanup), a clean Python app, one fixture per rule, and regression fixtures for an unrelated unmount handler, a key returned inside an object, and a Python client built through a factory. The literal-key test builds its fake key at runtime so this repository never contains a key-shaped string.

## Limits

These are pattern checks, not a type checker. They can miss a key passed through several variables, and they treat any `session_timeout` handling as a restart. Public code also over-represents hackathon projects, so the corpus counts describe public code, not Odyssey's customer base.
