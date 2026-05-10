/**
 * Internal-link helper that respects Astro's `base` config.
 *
 * Locally (no `BASE` env var, base="/"), this is a no-op.
 * On GitHub Pages deploy (base="/agentic-skill-behavioral-audit"),
 * this prefixes every absolute internal link with the base path.
 *
 * Usage:
 *   import { u } from "@/lib/url";
 *   <a href={u("/skills")}>Skills</a>
 *   <img src={u("/figures/fig-01.svg")} />
 */
export function u(path: string): string {
  if (!path) return path;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (path.startsWith("#") || path.startsWith("mailto:")) return path;
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  if (!path.startsWith("/")) return path;
  if (base && path.startsWith(base + "/")) return path;
  if (base && path === base) return path;
  return base + path;
}
