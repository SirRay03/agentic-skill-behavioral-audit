# Task — pinecone-mcp

## Skill identity

- **Maker / repo**: pinecone-io / skills
- **In-repo path**: `skills/pinecone-mcp`
- **Category**: meta / MCP-using
- **Role in sample**: novel transport stack — Model Context Protocol over stdio/HTTP — tests whether SKILL.md declares MCP server endpoints + whether trace surfaces MCP tool calls

## Prompt

```
Use pinecone-mcp to list available Pinecone indexes via the MCP server, then create a new serverless index named "audit-test-skill" with dimension=2, cloud=aws, region=us-east-1.
```

## Rationale

`pinecone-mcp` SKILL.md (106 lines) is a meta-skill teaching the agent to invoke 8 MCP tools (`list-indexes`, `describe-index`, `upsert-records`, `search-records`, etc.). The methodological interest is binary: does the agent route via MCP tool calls (invisible to syscall trace — Finding A territory), or does it shell out to Pinecone's REST API directly?

## Expected observable footprint

- **fs-reads**: SKILL.md, possibly `~/.config/pinecone/` if a config exists
- **fs-writes**: agent-infrastructure only if MCP-routed; otherwise none
- **subprocess**: none direct — MCP transport is stdio or HTTP
- **network hosts**: `mcp.pinecone.io` (HTTP MCP transport per SKILL.md), `api.pinecone.io` (indirect via tools), `controller.<region>.pinecone.io`
- **Methodological prediction**: most of the work happens via Anthropic-harness-routed `mcp__*` tool calls — invisible to strace/tcpdump. This is exactly the Finding A blind-spot pattern, in extreme form. The trace may show ZERO Pinecone-related observables despite the agent successfully completing the task.

## Caveats / simplifications

- No Pinecone API key provisioned — expect tool-call failures at the MCP server boundary. The failure mode itself is informative.
- MCP server probably not configured in our `.mcp.json` — agent will likely not have access at all, and will tell the user as much. **The "MCP not configured" failure is its own finding** — illustrates how a SKILL.md that mandates an MCP server can be entirely non-functional if the harness isn't pre-wired.
