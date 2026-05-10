import { marked } from "marked";

marked.setOptions({
  gfm: true,
  breaks: false,
});

/**
 * Render a markdown string to HTML at build time. Used for finding bodies
 * and analysis-doc excerpts that come in via the JSON content collection.
 */
export function renderMd(md: string): string {
  if (!md) return "";
  return marked.parse(md, { async: false }) as string;
}
