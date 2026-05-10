# Task — firecrawl-scrape

## Skill identity

- **Maker / repo**: firecrawl / cli
- **In-repo path**: `skills/firecrawl-scrape`
- **Category**: network (web scraping)
- **Role in sample**: broader network case than web-search; tests "does LLM predict only declared API or also dynamic third-party hosts"

## Prompt

```
Scrape https://example.com using firecrawl-scrape, extract the main content as markdown, save to ./.firecrawl/page.md.
```

## Rationale

Direct lift of the maker's documented example: `firecrawl scrape "https://example.com/pricing" --only-main-content -o .firecrawl/page.md`. Using example.com as the target makes the result deterministic (well-known stable HTML).

## Expected observable footprint

- **fs-reads**: `firecrawl` binary, possibly API key from `~/.firecrawl/` or env
- **fs-writes**: `./.firecrawl/page.md`
- **subprocess**: `firecrawl`
- **network hosts**: `api.firecrawl.dev` definitely; `example.com` only if scraping is client-side (interesting open question for the trace to resolve)

## Caveats / simplifications

- API key needed for production calls; with stub key, behaviour will be auth failure
- If api.firecrawl.dev does the actual fetching, example.com won't appear in our trace — that's a meaningful prediction-vs-observation gap to highlight
