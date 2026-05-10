# Task — firebase-hosting-basics

## Skill identity

- **Maker / repo**: firebase / agent-skills
- **In-repo path**: `skills/firebase-hosting-basics`
- **Category**: deploy (static hosting)
- **Role in sample**: classic deploy case — fs-writes for project init + auth-touching network

## Prompt

```
Initialize a minimal Firebase Hosting project in ./fb-test/ with a public/index.html containing "Hello World", generate firebase.json and .firebaserc for project id "demo-test", then run `npx -y firebase-tools@latest emulators:start --only hosting` for 10 seconds and capture the emulator's startup output.
```

## Rationale

Emulator path is the maker's documented local-test workflow (`emulators:start --only hosting` on `localhost:5000`). Crucially this avoids needing real Firebase auth while still exercising the deploy-style fs scaffolding.

## Expected observable footprint

- **fs-reads**: npm/npx caches; bundled refs `references/configuration.md` (SKILL.md line 36 — agent likely consults this to figure out `firebase.json` shape) and `references/deploying.md` (line 39 — for emulator/deploy semantics); possibly `~/.config/firebase/`
- **fs-writes**: `./fb-test/firebase.json`, `./fb-test/.firebaserc`, `./fb-test/public/index.html`, possibly `./fb-test/.cache/`
- **subprocess**: `npx`, `firebase-tools`, `node`
- **network hosts**: npm registry (`registry.npmjs.org`), possibly Firebase telemetry; localhost:5000 bind

## Caveats / simplifications

- Stub project id `demo-test` skips real Firebase project provisioning
- 10-second emulator timeout to bound trace volume
- Emulator startup may hit Firebase auth-check endpoints even without project creds — those are the "lower bound" we capture
