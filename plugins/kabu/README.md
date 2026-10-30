# Kabu for Claude Code and GitHub Copilot CLI

[Kabu](https://usekabu.com) puts your coding agent on your phone. The agent tells you when work finishes or fails,
asks before risky steps, lets you pick an option or type an answer from the Lock Screen, and shows a long run's
progress as a Live Activity. You need the Kabu app on your iPhone and Python 3.9 or later as `python3`.

| Part | What it does |
|---|---|
| `kabu-notify` skill | Teaches the agent when and how to notify and ask, with the `kabu` CLI |
| `bin/kabu` | The `kabu` CLI: one Python file, standard library only |
| `kabu` MCP server | `kabu mcp`: Kabu's MCP tools over stdio, signed in with your saved login |
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

Connect this computer once. Approve the code it prints in the Kabu app; its own key is then saved to
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

Or install it on your PATH: `curl -fsSL https://usekabu.com/kabu -o ~/.local/bin/kabu && chmod +x ~/.local/bin/kabu`.
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
`ask_human`, `wait_for_human_answer` and `upload_file_for_human`. Check it with `/mcp` in Claude Code or Copilot CLI.
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

## Troubleshooting

| Symptom | Fix |
|---|---|
| `missing_api_key` | Log in (above), or set `KABU_API_KEY`; then reconnect `kabu` in `/mcp`, or restart the session |
| `kabu: command not found` | Use the plugin's copy, as in Log in, or `python3 <plugin>/bin/kabu` |
| MCP server failed, or `HTTP 401` from a tool | Log in again: the key is missing or revoked (`kabu whoami` shows which is in use). Then reconnect `kabu` in `/mcp`, or restart |
| No push arrives | `kabu send "Test" --dry-run` shows what would be sent; check the app is signed in to the same account |
| An ask returns exit 20 | It expired unanswered; raise `--expires-in` (default 300 seconds) |
| No hook pushes | Set `KABU_HOOKS=1` before starting the agent, then restart it |

`KABU_BASE_URL`, `KABU_PROJECT`, `KABU_AGENT` and `KABU_CONFIG_PATH` override the defaults; see `kabu --help`.

## License

MIT, see [LICENSE](LICENSE). The Kabu name and logo, including `.claude-plugin/icon.png`, are trademarks of NexAI Tech
and are not licensed under MIT; the icon is here only to show this plugin in plugin lists.
