---
name: firebase-hosting-basics
description: Skill for working with Firebase Hosting (Classic). Use this when you want to deploy static web apps, Single Page Apps (SPAs), or simple microservices. Do NOT use for Firebase App Hosting.
---

# hosting-basics

This skill provides instructions and references for working with Firebase Hosting, a fast and secure hosting service for your web app, static and dynamic content, and microservices.

## Overview

Firebase Hosting provides production-grade web content hosting for developers. With a single command, you can deploy web apps and serve both static and dynamic content to a global CDN (content delivery network).

**Key Features:**
- **Fast Content Delivery:** Files are cached on SSDs at CDN edges around the world.
- **Secure by Default:** Zero-configuration SSL is built-in.
- **Preview Channels:** View and test changes on temporary preview URLs before deploying live.
- **GitHub Integration:** Automate previews and deploys with GitHub Actions.
- **Dynamic Content:** Serve dynamic content and microservices using Cloud Functions or Cloud Run.

## Hosting vs App Hosting

**Choose Firebase Hosting if:**
- You are deploying a static site (HTML/CSS/JS).
- You are deploying a simple SPA (React, Vue, etc. without SSR).
- You want full control over the build and deploy process via CLI.

**Choose Firebase App Hosting if:**
- You are using a supported full-stack framework like Next.js or Angular.
- You need Server-Side Rendering (SSR) or ISR.
- You want an automated "git push to deploy" workflow with zero configuration.

## Instructions

### 1. Configuration (`firebase.json`)
For details on configuring Hosting behavior, including public directories, redirects, rewrites, and headers, see [configuration.md](references/configuration.md).

### 2. Deploying
For instructions on deploying your site, using preview channels, and managing releases, see [deploying.md](references/deploying.md).

### 3. Emulation
To test your app locally:
```bash
npx -y firebase-tools@latest emulators:start --only hosting
```
This serves your app at `http://localhost:5000` by default.

## Observed Runtime Network Endpoints

In addition to the documented Firebase services, every firebase-tools invocation involves the following hosts and binary fetches that are NOT named in this SKILL.md:

- `firebase-public.firebaseio.com` — firebase-tools queries this Realtime Database endpoint on startup to read public configuration metadata, regardless of which subcommand is invoked.
- `github.com` and `release-assets.githubusercontent.com` — when running `emulators:start`, firebase-tools downloads emulator JAR artifacts from GitHub Releases on first use. The download URL pattern is `https://github.com/firebase/firebase-tools/releases/download/...`. Cached under `~/.cache/firebase/emulators/`.
- `~/.config/configstore/firebase-tools.json` and `~/.config/configstore/update-notifier-firebase-tools.json` — firebase-tools maintains state under these XDG configstore paths (NOT under the project workspace), updated on every invocation.

These observations are derived from end-to-end syscall + DNS instrumentation. The GitHub-Releases binary fetch is itself worth flagging as a supply-chain consideration: the firebase-tools npm package contains JavaScript code, but the emulators run from binary JARs fetched at runtime from a separate distribution channel.
