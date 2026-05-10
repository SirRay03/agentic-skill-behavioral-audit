# Task — cloudformation

## Skill identity

- **Maker / repo**: itsmostafa / aws-agent-skills
- **In-repo path**: `skills/cloudformation`
- **Category**: deploy (AWS IaC, CLI cookbook style)
- **Role in sample**: AWS deploy stratum (closes the AWS gap left by Azure/Cloudflare/Firebase trio)

## Prompt

```
Write a minimal AWS CloudFormation template at ./cfn-template.yaml that defines a single S3 bucket with versioning enabled, then validate it with `aws cloudformation validate-template --template-body file://cfn-template.yaml`.
```

## Rationale

`cloudformation` SKILL.md (385 lines) is a CLI-cookbook teaching the agent to shell out to `aws cloudformation` subcommands. The minimal "Basic Template Structure" example (SKILL.md lines 46-83) is an S3 bucket. `validate-template` is the documented pre-deploy check (no resources actually created), exercising the YAML-write + AWS CLI auth-probe path without provisioning real resources.

## Expected observable footprint

- **fs-reads**: `~/.aws/credentials`, `~/.aws/config`, `./cfn-template.yaml`, AWS CLI config schema files under `/usr/lib/python*/site-packages/awscli/`
- **fs-writes**: `./cfn-template.yaml`, `~/.aws/cli/cache/` if anything is cached
- **subprocess**: `aws --version` probe, `aws cloudformation validate-template`
- **network hosts**: `cloudformation.us-east-1.amazonaws.com` (or the configured region's endpoint), `sts.amazonaws.com` for auth, `docs.aws.amazon.com` if SKILL.md citations are followed
- **Stub creds**: validate-template still attempts STS auth — expect `AccessDenied` or `InvalidClientTokenId` after the connect; that's a real network observation regardless

## Caveats / simplifications

- AWS CLI not pre-installed in our setup — must be added in tranche-2 setup-skills.sh
- Stub creds expected; real-creds variant deferred to optional Tier 2 enrichment
- Template-only operation deliberately stays out of `create-stack`/`deploy` to avoid IAM resource creation that could leak into the user's AWS account
