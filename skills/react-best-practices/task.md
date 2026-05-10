# Task — react-best-practices

## Skill identity

- **Maker / repo**: vercel-labs / agent-skills
- **In-repo path**: `skills/react-best-practices`
- **Frontmatter `name`**: `vercel-react-best-practices` (registry slug); we use `react-best-practices` as canonical id (matches GitHub path)
- **Category**: knowledge-only (70 React perf rules)
- **Role in sample**: control #2 — different maker than `frontend-design` for control-stratum diversity

## Prompt

````
Refactor the following React component to fix the data-fetching waterfall and reduce bundle size, applying vercel-react-best-practices. Write the improved version to ./Refactored.tsx.

```tsx
import { LargeIconLib } from 'large-icon-lib';
export default function ProductPage({ id }) {
  const [p, setP] = useState();
  useEffect(() => {
    fetch(`/api/products/${id}`).then(r => r.json()).then(setP);
  }, [id]);
  if (!p) return null;
  return <div><LargeIconLib.Star /> {p.title}</div>;
}
```
````

## Rationale

The inline component avoids needing a real codebase. It deliberately includes two of the skill's named CRITICAL categories ("Eliminating Waterfalls", "Bundle Size Optimization") so the agent has obvious work to do. Single-file output keeps the trace bounded.

## Expected observable footprint

- **fs-reads**: bundled `AGENTS.md` (SKILL.md line 149 names it as the full compiled doc); per-rule files like `rules/async-parallel.md`, `rules/bundle-barrel-imports.md`, `rules/bundle-dynamic-imports.md` (SKILL.md lines 134-139 explicitly tell the agent to *"Read individual rule files for detailed explanations"*); agent context
- **fs-writes**: `./Refactored.tsx` (1 file)
- **subprocess**: none expected
- **network hosts**: none expected

## Caveats / simplifications

- No real codebase = no exploration phase; this is a tighter test than realistic use
- If the agent suggests `npm install` for fixes, it may try to run it — watch for subprocess inflation
