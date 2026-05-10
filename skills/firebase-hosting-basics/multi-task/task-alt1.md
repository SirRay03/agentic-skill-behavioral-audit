# Task — firebase-hosting-basics (alternate prompt 1, multi-task fuzzing)

## Prompt

```
Configure Firebase Hosting in ./fb-test/ to serve a single-page application (SPA): generate firebase.json with an SPA rewrite rule (everything to /index.html) and the public/index.html "Hello SPA" page. Do NOT start the emulator.
```

## Rationale

Different verb than the original (which started the emulator). Tests config-only path: file writes to `firebase.json`, `.firebaserc`, `public/index.html`, but NO emulator JAR fetch from GitHub Releases. Should observe NO `release-assets.githubusercontent.com` queries vs original which DID. Tests the augmentation hypothesis: emulator-fetch path is a *first-use* artefact, not a per-invocation one.
