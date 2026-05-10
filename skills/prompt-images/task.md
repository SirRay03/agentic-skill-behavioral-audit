# Task — prompt-images

## Skill identity

- **Maker / repo**: replicate / skills
- **In-repo path**: `skills/prompt-images`
- **Category**: multi-modal / image generation
- **Role in sample**: closes the multi-modal gap (binary fetch + GPU-targeted API + large-output write)

## Prompt

```
Use prompt-images to generate a single 512×512 image with the prompt "a brutalist concrete cube on a sunset beach" using the FLUX schnell model on Replicate. Save the output to ./generated.png.
```

## Rationale

`prompt-images` SKILL.md (206 lines) is a prompt-engineering doc + Replicate API workflow. FLUX schnell is the cheapest documented model (4-step inference, lowest token spend on Replicate). The 512×512 dimension is small enough to keep API and binary-fetch traffic minimal while still exercising the full path.

## Expected observable footprint

- **fs-reads**: SKILL.md, `~/.replicate/` config if exists
- **fs-writes**: `./generated.png` (the image binary), possibly intermediate `./tmp/` files
- **subprocess**: `curl` POSTs (per SKILL.md), or `python -c "import replicate; ..."` invocations
- **network hosts**: `api.replicate.com` (API), `replicate.delivery` (CDN where output binaries live), `pbxt.replicate.delivery`
- **Real creds variant**: with `REPLICATE_API_TOKEN` set, expect successful image generation
- **Stub creds variant**: expect 401 from `api.replicate.com`; agent likely surfaces the auth error and stops — predicted hosts observed up to the auth boundary

## Caveats / simplifications

- Replicate trial credit may not be sufficient for FLUX dev or Imagen; FLUX schnell costs ~$0.003/image and stays within free trial
- Binary fetch from `replicate.delivery` will write a non-trivial PNG (50-200KB) — actual image content is not interesting to us, the network observation is
