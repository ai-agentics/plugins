# Kabu for Claude Code and GitHub Copilot CLI

[Kabu](https://usekabu.com) puts your coding agent on your phone. The agent tells you when work finishes or fails,
asks before risky steps, lets you pick an option or type an answer from the Lock Screen, and reports a long run's
session progress. You need the Kabu app on your iPhone and Python 3.9 or later as `python3`.

| Part | What it does |
|---|---|
| `kabu-notify` skill | Teaches the agent when and how to notify and ask, with the `kabu` CLI |
| `bin/kabu` | The `kabu` CLI: one Python file, standard library only |
| `kabu` MCP server | `kabu mcp`: Kabu's MCP tools over stdio, signed in with your saved login |
| Presence, on by default | The app shows whether the agent is working, idle, waiting for you at the computer or gone (`KABU_PRESENCE=0` turns it off) |
| Hooks, off by default | A push when the agent finishes a turn or needs your input (`KABU_HOOKS=1`) |

## Install

Claude Code:

```text
/plugin marketplace add ai-agentics/plugins
/plugin install kabu@ai-agentics
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add ai-agentics/plugins
copilot plugin install kabu@ai-agentics
```

Then log in, below, and restart the session, so the skill, the MCP server and the hooks load with your login.

## Log in

Connect this computer once. In the Kabu app, open Connect a computer and enter the code it prints (or open the link
it prints in a browser); an admin or owner of the workspace must approve it. Its own key is then saved to
`~/.config/kabu/config.json` (mode 600), and the skill, the MCP server and the hooks all use it. No key goes in any
plugin or agent config.

```bash
kabu login --device
```

The simplest way is to ask the agent to log you in to Kabu: it runs that command with the plugin's copy of the CLI and
shows you the code. Claude Code puts the plugin's `bin/` on the PATH of the agent's shell, not of your terminal. To run
`kabu` in your own terminal, use the plugin's copy:

| Client | The CLI |
|---|---|
| Claude Code | `~/.claude/plugins/cache/ai-agentics/kabu/<version>/bin/kabu` |
| Copilot CLI | `~/.copilot/installed-plugins/ai-agentics/kabu/bin/kabu` |

Or install it on your PATH: `mkdir -p ~/.local/bin && curl -fsSL https://usekabu.com/kabu -o ~/.local/bin/kabu && chmod +x ~/.local/bin/kabu`.
Check the login with `kabu whoami`.

## Use it

Ask in plain words: "tell me on my phone when the tests finish", "ask me before you deploy". The agent loads the
`kabu-notify` skill and runs commands such as:

```bash
kabu send "Tests passed" "412 passed, 0 failed"
kabu ask "Deploy v1.4.2 to prod?" "Canary green for 30 min"     # exit 0 approved, 10 rejected
kabu ask "Which environment?" -c staging -c production         # the pick is in the JSON: option
kabu session start --title "Migrate billing" --headline "Copying tables" --progress 1/4
```

Every command prints JSON; `kabu --help` and `kabu COMMAND --help` list the options, limits and exit codes.

## MCP

The plugin starts an MCP server named `kabu` as `python3 bin/kabu mcp`. It relays MCP over stdio to
`https://usekabu.com/mcp` (or `KABU_BASE_URL`) with your saved key, so the agent also gets the tools `notify_human`,
`ask_human`, `wait_for_human_answer` and `upload_file_for_human`. For the tools that take a project it fills in the
one your session's folders name, at each call, unless your key is bound to a project. Check it with `/mcp` in Claude
Code or Copilot CLI.
It reads the login saved by `kabu login --device`, which works in both clients. Settings such as `KABU_API_KEY` and
`KABU_BASE_URL` reach it only if the client passes your shell's environment on to its MCP servers, so prefer the
saved login.

## Hooks

Off unless `KABU_HOOKS=1` is set in the environment the agent starts from:

| When | Push | Claude Code event | Copilot CLI event |
|---|---|---|---|
| The agent finishes a turn | "Turn finished", with the first 300 characters of the agent's last message when the client sends it | `Stop` | `agentStop` |
| The agent needs you: a permission prompt, a question, or a link to open, its own or a subagent's | "Needs your input", with the prompt | `Notification` | `notification` |

The hooks run in the background and print nothing, so they never slow or block the agent; a failed push is dropped.
The text they send, that excerpt or the prompt, leaves your machine and shows on your Lock Screen: leave the hooks
off if your agent may print secrets.
They need a POSIX shell (macOS or Linux). If you already use Kabu's older hooks from `~/.kabu/hooks`, leave
`KABU_HOOKS` unset to avoid two pushes.

## Presence

On by default. The app shows, on Threads and Agents, whether each agent session is working, idle (ready for a prompt),
waiting for you at the computer (a permission prompt) or gone. The plugin's hooks write one small file per event in a
private folder of yours on this computer (in its temp folder); they never read the event, never call the network and
start no program, so they add about a millisecond to each event. One `kabu presence run` per computer, started by the
hooks and gone 10 minutes after the last session ends, sends the state about once a minute, and at once when it
changes.

What leaves your computer: the state (working, idle, waiting at the computer, gone), ids made from a hash (never the
client's own session id), the client's name (`claude-code`) and the project the session runs in, as `kabu send` already
sends with every message. Never a prompt, a file path, a tool name, a title or your computer's name. `kabu send` and
`kabu ask` in the same session go in that session.

| To | Run |
|---|---|
| See what it reports | `kabu presence status` |
| Turn it off on this computer | `kabu presence off` (`kabu presence on` turns it back on) |
| Turn it off for one agent | Set `KABU_PRESENCE=0` in the environment the agent starts from |

Without the plugin, `kabu presence install --harness claude` (or `--harness copilot`) adds the same hook to the
client's settings, after a backup; `kabu presence uninstall` takes it out. Use one or the other.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `missing_api_key` | Log in (above), or set `KABU_API_KEY`; then reconnect `kabu` in `/mcp`, or restart the session |
| `kabu: command not found` | Use the plugin's copy, as in Log in, or `python3 <plugin>/bin/kabu` |
| MCP server failed, or `HTTP 401` from a tool | Log in again: the key is missing or revoked (`kabu whoami` shows which is in use). Then reconnect `kabu` in `/mcp`, or restart |
| No push arrives | `kabu send "Test" --dry-run` shows what would be sent; check the app is signed in to the same account |
| Messages land in another project | The project is the one of the folder the agent session started in, whatever folder a command runs in; `kabu whoami` shows it and, in `project_source`, why. Set `KABU_PROJECT` to choose another |
| An ask returns exit 20 | It expired unanswered; raise `--expires-in` (default 300 seconds) |
| No hook pushes | Set `KABU_HOOKS=1` before starting the agent, then restart it |
| The app shows no presence | `kabu presence status`: `enabled`, a `lanes` entry for the session and `last_beat` without an `error`; log in if it is `missing_api_key` |

`KABU_BASE_URL`, `KABU_PROJECT`, `KABU_AGENT` and `KABU_CONFIG_PATH` override the defaults; see `kabu --help`.

## License

MIT, see [LICENSE](LICENSE). The Kabu name and logo, including `.claude-plugin/icon.png`, are trademarks of NexAI Tech
and are not licensed under MIT; the icon is here only to show this plugin in plugin lists.
