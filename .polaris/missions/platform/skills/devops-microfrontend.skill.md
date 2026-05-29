---
name: DevOps Micro-Frontend Skill
description: |
  Extra rules that apply ONLY when the service is classified as Micro-Frontend
  (multi-app monorepo with separate frontend apps deployed as distinct
  Kubernetes deployments). Loaded on demand by /polaris.devops; not loaded
  for single-image services.
---

## MICRO-FRONTEND DEPLOYMENT STRUCTURE (HARD RULE)

For Micro-Frontend services:

- Each micro-frontend application MUST be deployed as:
  - A separate Kubernetes Deployment
  - Containing EXACTLY ONE container

Rules:
1. The agent MUST generate one `deployments[]` entry per micro-frontend app.
2. Each `deployments[]` entry MUST contain exactly ONE container, and the container name MUST match the deployment name.
3. The agent MUST NOT create a single Deployment with multiple containers, and MUST NOT group multiple micro-frontends into the same pod.
4. Shared configuration: AppConfig and KeyVault references remain shared. `envFrom` MUST be identical across all deployments.

### Conditional Build Logic (CRITICAL)

For micro-frontend Docker builds:
- Each micro-frontend app MUST have its own build job.
- Each build job MUST have a condition that checks for changes.
- A build job SHOULD ONLY execute if:
  - Changes are detected in the app's source folder, OR
  - The user manually triggers with a "force build all" input.
- By DEFAULT, do NOT build all apps on every commit.

Implementation:
- Use GitHub Actions path filters (or equivalent).
- Each build job condition: `if: contains(github.event.changes, 'apps/<app-name>/**') || inputs.force_build_all`.
- Structure the docker workflow to detect changed paths and map them to specific build jobs.
- Skip builds for unchanged apps.

Example structure:
```yaml
jobs:
  detect-changes:
    outputs:
      app1_changed: ${{ steps.filter.outputs.app1 }}
      app2_changed: ${{ steps.filter.outputs.app2 }}

  build-app1:
    needs: detect-changes
    if: needs.detect-changes.outputs.app1_changed == 'true' || inputs.force_build_all

  build-app2:
    needs: detect-changes
    if: needs.detect-changes.outputs.app2_changed == 'true' || inputs.force_build_all
```

This ensures efficient builds and prevents unnecessary Docker image creation.

## MICRO-FRONTEND MULTI-IMAGE WORKFLOW HANDLING (CRITICAL)

For Micro-Frontend services with MULTIPLE containers, the agent MUST ensure ALL discovered micro-frontend images are properly handled in ALL workflow files, not just the build workflow.

### Mandatory file updates

| Workflow file | What MUST be present |
|---|---|
| `docker.acr-images.promote-{{ .ServiceName }}.yml` | A promote step (or job) for EACH discovered micro-frontend image. Image names MUST match those discovered from the Dockerfile. Each image is promoted from the devops registry to the target registry with its correct tag. |
| `docker.step.build-push-{{ .ServiceName }}.yml` | Build steps for ALL discovered images. Each container has its own build configuration with conditional logic per container. |
| `helm.step.{{ .ServiceName }}.deploy.yml` | Image tag handling for ALL discovered images. Image tags set for ALL containers in the values file. `Get Docker Image show-tags` for the micro-frontend-docker registry and `Replace tokens in values files` steps MUST handle the image tag for every container. |
| `helm/{{ .ServiceName }}/values-{{ .ServiceName }}.yml` | Separate `deployments[]`, `service[]`, and ingress-path entries for EACH container. Each deployment has a unique name matching its container, exactly one container, and the correct image repository and tag placeholder. Each service routes to its corresponding deployment; each ingress path routes to its corresponding service. |

### BGM workflow files (Blue-Green deployment)

The following files MUST handle ALL discovered images:

| File | Requirement |
|---|---|
| `bgm.helm.step.{{ .ServiceName }}.deploy.yml` | Image tag handling for ALL containers. `Get Docker Image show-tags` for EACH container. Replace tokens in values files for EACH container's image tag. |
| `bgm.helm.lwr.{{ .ServiceName }}.deploy.yml` | Pass image information for ALL containers; handle deployment of ALL discovered images. |
| `bgm.helm.upr.{{ .ServiceName }}.deploy.yml` | Pass image information for ALL containers; handle deployment of ALL discovered images. |

Pattern: if a service has 2 containers (e.g. `admin`, `employee`), every BGM workflow MUST handle both images: image-tag retrieval steps for BOTH, helm value replacement for BOTH, deployment orchestration for BOTH.

### CRITICAL execution rules

1. After Dockerfile analysis discovers multiple containers, the agent MUST immediately update ALL workflow files above (docker, helm, AND BGM workflow files). The agent MUST NOT assume single-image structure.
2. If ANY workflow file is missing multi-image handling: make the change to that file.

This rule is NON-NEGOTIABLE. Any violation MUST be corrected before creating a PR.
