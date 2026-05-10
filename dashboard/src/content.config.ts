// Content collections — Astro 5 syntax.
// We use `file` loaders pointed at build-time-generated JSON under
// src/data/generated/ rather than glob-loading markdown, because the audit
// data is structured and lives outside src/.
//
// Schemas are intentionally permissive (passthrough on the heavy fields)
// because per-skill prediction/policy JSON shapes differ across the
// production / mutation / adversarial / augmented classes. We only validate
// the fields the dashboard pages directly consume.

import { defineCollection, z } from "astro:content";
import { file } from "astro/loaders";

const skillCluster = z.enum([
  "high-f1",
  "low-f1",
  "mid-f1",
  "no-network",
  "augmented",
  "mutation",
  "adversarial",
]);

const skills = defineCollection({
  loader: file("src/data/generated/skills.json"),
  schema: z
    .object({
      id: z.string(),
      name: z.string(),
      owner: z.string().nullable(),
      repo: z.string().nullable(),
      category: z.string(),
      role: z.string(),
      class: z.enum(["production", "mutation", "adversarial", "augmented"]),
      cluster: skillCluster,
      f1: z.object({
        paths_read: z.number().nullable(),
        paths_written: z.number().nullable(),
        hosts: z.number().nullable(),
      }),
      f1_status: z.object({
        paths_read: z.enum(["ok", "match", "miss", "no-data"]),
        paths_written: z.enum(["ok", "match", "miss", "no-data"]),
        hosts: z.enum(["ok", "match", "miss", "no-data"]),
      }),
      has_prediction: z.object({
        orig: z.boolean(),
        fresh: z.boolean(),
        codex: z.boolean(),
      }),
      has_trace: z.object({
        orig: z.boolean(),
        codex: z.boolean(),
        realcreds: z.boolean(),
        multitask: z.boolean(),
        stability: z.boolean(),
        effort: z.boolean(),
      }),
      has_policy: z.boolean(),
      skill_md_excerpt: z.string(),
      task_md: z.string(),
      prediction_summary: z.object({
        n_paths_read: z.number(),
        n_paths_written: z.number(),
        n_hosts: z.number(),
        n_subprocesses: z.number(),
        hosts: z.array(z.string()),
        rationale: z.string().nullable(),
      }),
      observed_summary: z.object({
        n_paths_read: z.number(),
        n_paths_written: z.number(),
        n_hosts: z.number(),
        hosts: z.array(z.string()),
      }),
    })
    .passthrough(),
});

const findings = defineCollection({
  loader: file("src/data/generated/findings.json"),
  schema: z.object({
    id: z.string(),
    slug: z.string(),
    title: z.string(),
    one_line: z.string(),
    section: z.string(),
    layer: z.array(
      z.enum([
        "L1-static",
        "L2-llm",
        "L3-runtime-claude",
        "L4-runtime-codex",
        "policy-design",
        "methodology",
      ])
    ),
    pattern: z.enum([
      "vendor-cli-underdeclaration",
      "agent-runtime-opacity",
      "adversarial-maintainer",
      "methodology",
    ]),
    severity: z.enum(["high", "medium", "low", "info"]),
    body_md: z.string(),
    related_skills: z.array(z.string()),
    key_numbers: z.array(
      z.object({
        label: z.string(),
        value: z.string(),
      })
    ),
  }),
});

const analysis = defineCollection({
  loader: file("src/data/generated/analysis.json"),
  schema: z
    .object({
      slug: z.string(),
      title: z.string(),
      body_md: z.string(),
    })
    .passthrough(),
});

export const collections = { skills, findings, analysis };
