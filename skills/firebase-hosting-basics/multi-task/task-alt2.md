# Task — firebase-hosting-basics (alternate prompt 2, multi-task fuzzing)

## Prompt

```
Add custom HTTP headers to ./fb-test/firebase.json so all .html files are served with `Cache-Control: max-age=300, public` and the `X-Content-Type-Options: nosniff` security header. Use the `headers` array in firebase.json per the documented schema.
```

## Rationale

Pure-config edit task — no install, no emulator, no provisioning. Tests whether the agent reads `references/configuration.md` (the bundled sibling that documents firebase.json schema) before writing the config. Should observe ONLY the SKILL.md and the references/* sibling reads; minimal network surface (no Firebase API or emulator JAR fetch).
