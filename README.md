# ai-agentics plugins

Plugins for coding agents. Each one works in Claude Code and in GitHub Copilot CLI.

## Add the marketplace

Claude Code:

```text
/plugin marketplace add ai-agentics/plugins
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add ai-agentics/plugins
```

## Plugins

| Plugin | What it does | Install |
|---|---|---|
| [kabu](plugins/kabu) | Reach yourself on your phone from your coding agent: notifications, approvals, choices and typed replies, Live Activity progress, and Kabu's MCP tools | `/plugin install kabu@ai-agentics`, or `copilot plugin install kabu@ai-agentics` |

## Layout

- `.claude-plugin/marketplace.json` is the catalogue. Claude Code and Copilot CLI both read it.
- Each plugin lives in `plugins/<name>/`, with its manifest in `.claude-plugin/plugin.json`. Its skills are named
  `<name>-…`, so they never collide with another plugin's.

## How plugins arrive

A plugin's own repository is its source of truth. Each release arrives as a pull request that touches only
`plugins/<name>/` and that plugin's entry in the catalogue. The Validate workflow checks every manifest on each pull
request.

## License

MIT, see [LICENSE](LICENSE). Each plugin also carries its own licence, and product names and logos stay their owners'.
