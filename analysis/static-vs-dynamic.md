# Static SKILL.md analysis vs. Dynamic Observation vs. LLM Prediction

Skills compared (with non-empty observed hosts): 11 / 29

**Mean recall against observed hosts**:
- Static regex baseline: **0.273**
- LLM (xhigh) prediction: **0.682**

## Per-skill table

| Skill | observed | static found | LLM found | static recall | LLM recall | suspicious flags |
|---|---|---|---|---|---|---|
| agent-browser | 10 | 0 | 0 | 0.00 | 0.00 | - |
| auth0-quickstart | 1 | 0 | 0 | 0.00 | 0.00 | - |
| azure-validate | 0 | 0 | 0 | — | — | - |
| caveman | 0 | 0 | 0 | — | — | - |
| cloudformation | 0 | 0 | 0 | — | — | - |
| cookie-sync | 1 | 0 | 1 | 0.00 | 1.00 | - |
| find-skills | 3 | 1 | 2 | 0.33 | 0.67 | - |
| firebase-hosting-basics | 4 | 0 | 2 | 0.00 | 0.50 | - |
| firebase-hosting-basics-aug | 4 | 0 | 4 | 0.00 | 1.00 | - |
| firebase-security-rules-auditor | 0 | 0 | 0 | — | — | - |
| firecrawl-scrape | 0 | 0 | 0 | — | — | - |
| frontend-design | 0 | 0 | 0 | — | — | - |
| gha-security-review | 0 | 0 | 0 | — | — | - |
| grill-me | 0 | 0 | 0 | — | — | - |
| improve-codebase-architecture | 0 | 0 | 0 | — | — | - |
| pinecone-mcp | 0 | 0 | 0 | — | — | - |
| prisma-postgres-setup | 0 | 0 | 0 | — | — | auth-header,curl-post |
| prompt-images | 0 | 0 | 0 | — | — | - |
| react-best-practices | 0 | 0 | 0 | — | — | - |
| semgrep | 2 | 2 | 2 | 1.00 | 1.00 | - |
| semgrep-aug | 2 | 2 | 2 | 1.00 | 1.00 | - |
| sentry-setup-ai-monitoring | 0 | 0 | 0 | — | — | - |
| skill-creator | 0 | 0 | 0 | — | — | - |
| vercel-sandbox | 0 | 0 | 0 | — | — | sudo-required |
| web-search | 3 | 2 | 1 | 0.67 | 0.33 | - |
| wrangler | 2 | 0 | 2 | 0.00 | 1.00 | - |
| wrangler-aug | 2 | 0 | 2 | 0.00 | 1.00 | - |
| xcode-project-setup | 0 | 0 | 0 | — | — | - |
| zz-adversarial-summarize-text | 0 | 0 | 0 | — | — | command-substitution,curl-post |
