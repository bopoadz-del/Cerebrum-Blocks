# FLEET_OPS / PROMPT_STANDARD_v2.md — supersedes PROMPT_STANDARD.md (Sep 4 2026)
Same shape (TARGET / DO / EXIT / FORBIDDEN), three rails changed by the owner:

R8  No asking when the path is obvious. "Say go" for anything inside DO is forbidden.
    Before reporting a missing tool, find the no-shell path (CI, config, dependabot).
R9  CONTINUOUS. "REPORT then STOP" is dead. Keep a RUNNING LOG, one line per landed
    step, in FLEET_OPS/artifacts/<lane>/RUNLOG.md (append-only). Stop only at campaign
    end, an owner-gated item, or a genuinely dead tool.
R10 RETRY CAP: 3 attempts per failing test/gate/step. Fourth = write it to
    STATE.failures as OPEN with the evidence gap and the attempted repairs, SKIP to the
    next step, return to it after the queue. Loop forever on the campaign; never loop
    forever on one step. Escalation is a log line, not a pause.

Mandatory artifacts per lane (the harness, not prose):
  STATE  FLEET_OPS/state/<LANE>_STATE.json — goal, done_when, current_step,
         artifacts, decisions, failures(OPEN/CLOSED), pending(owner), rollback_point.
         Updated after every landed step. A new session inherits STATE, not the chat.
  RECEIPT in every PR body: tests passed/failed, mutants run/survivors (UNPRODUCED
         if no runner — never invented), retries, tools used, rollback SHA, deploy SHA.
  TWINS  every prose rule gets a mechanical check in CI (see campaign orders).
