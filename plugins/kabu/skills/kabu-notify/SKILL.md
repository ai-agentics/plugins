---
name: kabu-notify
description: Notify and ask the user on their phone through Kabu. Use when the user wants to be told or asked on their phone (notify me, ping me, ask me before you...), when long work finishes, fails or is blocked while they may be away, before an irreversible or production action that needs their approval, when they must pick an option or type an answer, and to show a long run's session progress. Runs the kabu CLI that ships with this plugin.
allowed-tools: Bash(kabu:*)
---

# Kabu: notify and ask the user

`kabu` pushes to the user's phone (the Kabu app) and, for a question, waits for their answer. Use it instead of a
terminal prompt when the user may be away, and instead of finishing long work silently.

## Run it

The CLI ships with this plugin, in its `bin/` folder.

- Claude Code: run the commands below as written; Claude Code puts that folder on PATH. If `kabu` is not found, use
  `python3 "${CLAUDE_PLUGIN_ROOT}/bin/kabu"` in its place.
- Copilot CLI: in every command below, put `python3 "<base>/../../bin/kabu"` in place of `kabu`, where `<base>` is the
  absolute base directory Copilot gives for this skill. Copilot fills in no plugin path in skills.

Each command prints one JSON object on stdout; an error is one JSON line on stderr with a `hint`, which is the fix.
On `missing_api_key`, connect this computer yourself: start `kabu login --device` as a background command (it waits up
to 10 minutes), show the user what it prints on stderr (the code to enter in the Kabu app under Connect a computer,
or a link that approves it in a browser; an admin or owner of the workspace must approve it), and carry on once they
have.
If the `kabu` MCP server had failed for want of a key, ask them to reconnect it in `/mcp`. Never ask for, print or pass
an API key yourself.

## When

- Notify when work of more than a few minutes ends, fails or is blocked, and at milestones of a long run; not every step.
- Ask before anything irreversible or production-facing (deploys, migrations, deleting data, force-pushes, messages to
  other people) and when only the user can decide. No answer is never a yes.
- Title up to 120 characters, detail in the message (8192). Never send secrets; `--sensitive` hides the content on the
  Lock Screen.

## Notify

```bash
kabu send "Tests passed" "412 passed, 0 failed in 3m12s"
kabu send "Deploy failed" "Migration 42 timed out" --priority high --link "Logs=https://ci.example.com/runs/77"
kabu send "Nightly report" "All jobs green" --file report.png --field env=prod --field duration=14m
git diff --stat | kabu send "Ready for review" -
```

`-` as the message reads it from stdin; `--diff -`, `--code -` and `--quote -` read a block from stdin instead.
It prints `{"ok": true, "id": "msg_…", "status": "sent", "attachments": 0, "project": "…", "project_source": {…},
"session": null}`.

## Ask

`kabu ask` blocks until the user answers or the ask expires (`--expires-in`, default 300 seconds), so give the shell
call a longer timeout (Claude Code: 600000 ms).

| To | Run | Then |
|---|---|---|
| Approve or reject | `kabu ask "Deploy v1.4.2 to prod?" "Canary green for 30 min"` | exit 0 approved, 10 rejected |
| Approve an exact action | add `--action db.migrate --args '{"version": 42}' --irreversible` | same |
| Pick one | `kabu ask "Which environment?" -c staging -c production` | read `option` |
| Pick several | `kabu ask "Which checks?" -c lint -c tests -c e2e --type multi` | read `choices` |
| Get a typed answer | `kabu ask "Name for the release?" --type text` | read `text` |

The answer is one JSON object with `outcome`, `decision`, `option`, `choices` and `text`. A choice exits 0 whatever
is picked, so branch on `option`; for yes or no, use the approve-or-reject form, not `-c yes -c no`. `option` is the
picked option's id: its label in lower case, with `_` for every character but an ASCII letter or digit and none at
either end (`-c "Roll back"` gives `roll_back`, `-c "Ship it."` gives `ship_it`). For a label with punctuation or
accents, set your own id: `-c "eu:Prod (EU)"` answers `eu`.

Exit codes: `0` approved, or a choice or text answered; `10` rejected, or a typed reply to an approve-or-reject ask
(read `text`); `20` expired with no answer; `21` cancelled, or `ask_gone`: deleted with its project, so ask again only
if you still need the answer; `2` bad command, nothing sent (fix it from the hint); `3` network or API error, or an
answer kabu does not know. Only `0` is a go: on any other code, do not act. A `3` error with an `id` means the ask is
still open: run its hint, `kabu status ID --wait 50`, and never ask again.

To wait longer than one tool call allows: `kabu ask "…" --no-wait --expires-in 3600` prints the `id` (`msg_…`). Then
run `kabu status msg_… --wait 50` until `status` is no longer `pending`. It exits 0 whatever the answer, so read it:
when `status` is `answered`, an approve-or-reject ask is a go only if `resolution.decision` is `approve`, and a pick or
a typed answer is in `resolution.option`, `resolution.options` or `resolution.text`. `expired` and `cancelled` mean no
answer.

## Show session progress

```bash
kabu session start --title "Migrate billing to v2" --headline "Copying tables" --progress 0/4
```

It prints the session: keep its `id` (`ses_…`) and pass it to every later call, as a shell variable may not survive
between calls.

```bash
kabu session update ses_… --headline "Running tests" --progress 2/4
kabu send "Tables copied" "4 of 4 verified" --session ses_…
kabu session end ses_… --outcome success --summary "PR #12 opened"
```

`--outcome` is `success`, `failure` or `cancelled`. Messages sent with `--session` group under it in the app. If a
send prints `session_gone`, that session was deleted with its project: kabu leaves the id out from then on and puts
later messages in a fresh session, whose id each output gives in `session`.

## Check first

- `kabu whoami`: what the key may do, and the project and agent kabu sends as. The project is the one the folder
  your session started in names, wherever you run kabu, and a scratch folder in `/tmp` never names one;
  `project_source` says why. Pass `--project`, or set `KABU_PROJECT`, only to send somewhere else.
- `--dry-run` on `send` or `ask`: the API checks it and shows the push; nothing is sent.
- `kabu COMMAND --help`: every option and its limit.

## MCP tools

The plugin also runs the `kabu` MCP server (`kabu mcp`, with the same login): `notify_human`, `ask_human`,
`wait_for_human_answer` and `upload_file_for_human`. Use the CLI or the tools for a message, not both. For the tools
that take a project, `kabu mcp` fills in the one your session's folders name, at each call, unless your key is bound
to a project; the server names the agent after your client. Pass either only to override it.
`ask_human` and `wait_for_human_answer` wait 25 s; to wait until the human replies, pass `max_wait_seconds: 3600`.
If either still returns an `id`, call `wait_for_human_answer` with it again.
