# Task — web-search

## Skill identity

- **Maker / repo**: inference-skills / skills
- **In-repo path**: `tools/llm/web-search`
- **Category**: network (search, smallest expected surface)
- **Role in sample**: simple network case + harness validation gate

## Prompt

```
Use the web-search skill to find the current population of Stockholm, Sweden. Return the figure with the source URL.
```

## Rationale

Maker's documented example is `belt app run tavily/search-assistant --input '{"query": "..."}'`. We use the same shape with a small factual query. The expected network footprint (inference.sh + Tavily/Exa) is small and well-bounded — ideal for the harness validation gate (P2).

## Expected observable footprint

- **fs-reads**: `belt` CLI binary path, possible auth token cache (`~/.config/belt/` or similar)
- **fs-writes**: minimal (response possibly cached to a temp dir)
- **subprocess**: `belt`
- **network hosts**: `inference.sh`, plus one of `api.tavily.com` / `api.exa.ai` (resolved server-side, may not appear in trace if proxied)

## Caveats / simplifications

- If `belt` requires auth (`belt login`), behaviour with empty creds is the captured signal
- Tavily/Exa hosts may be proxied through inference.sh, in which case the trace shows only inference.sh — that itself is a finding about how the LLM should predict (declared upstream APIs may be invisible)
