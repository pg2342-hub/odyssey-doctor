# Corpus results

Run on 2026-11-19 with `python corpus/run_corpus.py`. Repositories were found with GitHub code search for the SDK import strings and are pinned to the commits in projects.csv. Repositories in the same group (copies of one project) count once. Results are aggregate only. OD002 (literal keys) is not reported for other people's public projects.

20 repositories, 17 distinct projects using the SDK

| Rule | Check | Projects |
|---|---|---|
| OD001 | API key reachable from browser code | 12 of 17 |
| OD003 | No restart when a stream hits the 150-second limit | 12 of 17 |
| OD004 | Connection never released | 0 of 17 |
| OD005 | No cleanup on page exit or component unmount | 1 of 17 |
| OD006 | Usage limits not handled | 17 of 17 |
| OD007 | Wrong Python package | 1 of 17 |
| OD009 | Server route hands the raw API key to the browser | 4 of 17 |
| OD008 | Recovery path needs an API key the client does not have | 0 of 17 |

Streaming projects (call startStream or start_stream): 12 of 17, and the 12 OD003 hits are exactly those 12. Projects using Simulations: 9 of 17. Python SDK projects: 5 of 17. Projects using client credentials: 1 of 17, and only to clean up old sessions.

Cleanup: 12 projects open a connection from browser code. 11 of them release it when the page closes or the component unmounts (5 through the useOdyssey hook, 6 in their own code). The one OD005 hit only disconnects when the user switches modes.

Last commits across the corpus run from 2026-01-23 to 2026-11-05. One large repository (eyeoverthink/fraynix) is cloned sparsely to its Odyssey code, set by the `paths` column in projects.csv.
