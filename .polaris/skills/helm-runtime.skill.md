---
name: Helm Runtime Skill
description: |
  Governs Kubernetes runtime structure.
---

  ----------------------------------------------------------------------
  ✔ HELM PLACEHOLDER NORMALIZATION
  ----------------------------------------------------------------------

    Helm values files use a special triple-brace placeholder format for image tags.
  
    After token replacement, the agent MUST normalize these placeholders.
  
    Supported pattern (EXACT):
  
      {{{ .ServiceName | replace "-" "_" | upper }}_IMAGE_TAG}
  
    Step 1: Apply ServiceName transform:
      If ServiceName = test-repo, then:
      {{{ .ServiceName | replace "-" "_" | upper }}_IMAGE_TAG}
      → {{{TEST_REPO_IMAGE_TAG}
  
    Step 2: Normalize triple braces to hash format:
      {{{TEST_REPO_IMAGE_TAG}
      → #{TEST_REPO_IMAGE_TAG}#
  
    Final result:
      tag: #{TEST_REPO_IMAGE_TAG}#
  
    Rules:
    - Applies to Helm values files (helm/*/values-*.yml)
    - The opening {{{ (triple brace) MUST be replaced with #{
    - The closing } MUST be replaced with }#
    - Final placeholder MUST be wrapped in #{ ... }#
    - This format allows Azure DevOps variable replacement
    - Any deviation from this pattern → STOP with clear error

  ----------------------------------------------------------------------  
  ✔ HELM RUNTIME CONFIGURATION RULES (MANDATORY)
  ---------------------------------------------------------------------- 
  
  For ALL services (including micro-frontends):
  
  - The Helm chart represents a SINGLE runtime unit.
  
  Rules:
  
  1. `envFrom` MUST be defined ONCE per release.
  2. Secrets and AppConfig references MUST NOT be duplicated
     per container.
  3. Micro-frontend classification MUST NOT result in:
       - Multiple envFrom blocks
       - Multiple secret references
       - Multiple AppConfig references

  4. envFrom MUST use {{ .DeploymentName }} token (MANDATORY):
     The envFrom section in Helm values MUST reference the deployment name
     from config/MainManifest.yml for configMapRef and secretRef names.

     Required structure:
     ```yaml
     envFrom:
       - type: configMapRef
         name: {{ .DeploymentName }}
         fullnameOverride: ""
       - type: secretRef
         name: {{ .DeploymentName }}
         fullnameOverride: ""
     ```

     Where {{ .DeploymentName }} is replaced with the actual deployment name
     from config/MainManifest.yml (e.g., "api", "ui", "worker").

     Example (for a repo with deployments[].name = "api"):
     ```yaml
     envFrom:
       - type: configMapRef
         name: api
         fullnameOverride: ""
       - type: secretRef
         name: api
         fullnameOverride: ""
     ```

     Rules:
     - The name field MUST use DeploymentName, NOT ServiceName
     - fullnameOverride MUST be set to "" (empty string)
     - Both configMapRef and secretRef MUST be present
     - For multi-deployment repos, each deployment's envFrom uses
       its own DeploymentName

  ----------------------------------------------------------------------
  ✔ NAME OVERRIDE RULES (MANDATORY)
  ----------------------------------------------------------------------

  The agent MUST use `nameOverride` by default for all deployments.

  Rules:

  1. `nameOverride` is the DEFAULT behavior.
     - Use: nameOverride: <service-name>
     - This allows Helm release name to be prepended
     - Resource names follow pattern: <release-name>-<nameOverride>

  2. `fullnameOverride` MUST ONLY be used when:
     - Explicitly requested in the user prompt
     - User says "use fullnameOverride" or similar

  3. If fullnameOverride is NOT explicitly requested:
     - ALWAYS use nameOverride
     - Do NOT set fullnameOverride at all

  4. Example values structure:

     # Correct (default behavior):
     nextApplication:
       nameOverride: my-service

     # Only if explicitly requested:
     nextApplication:
       fullnameOverride: exact-resource-name

  ----------------------------------------------------------------------
  ✔ INGRESS PATH STRUCTURE RULES (MANDATORY)
  ----------------------------------------------------------------------

  Ingress path MUST be deterministic and consistent with service type.

  1️⃣ Backend Service Ingress Rule:

  If application is classified as Backend Service:
  Ingress path MUST follow:
    /{{ .ServiceName }}/api


  Examples:

  /<service-name>/api
  /<another-service>/api

  Rules:
  - `/api` suffix is mandatory
  - No trailing slash
  - Lowercase only
  - No underscores
  - Must match Helm ingress exactly

  2️⃣ Frontend Service Ingress Rule:

  If application is classified as Frontend Service:
  Ingress path MUST follow:
    /{{ .ServiceName }}/<frontend-segment>


  Examples:

  /<service-name>/admin
  /<service-name>/employee
  /<service-name>/dashboard


  Rules:
  - Must NOT contain `/api`
  - Segment must reflect frontend module name
  - Lowercase only
  - No underscores
  - Must match Helm ingress exactly

  3️⃣ Micro-Frontend Ingress Rule

  If service is classified as Micro-Frontend:
  Discover ALL ingress paths from Dockerfile.

  Each ingress path MUST:
  - Follow frontend OR backend rule above
  - Be validated
  - Not be auto-generated blindly

  The agent MUST NOT assume:
  - Only /ServiceName exists
  - Only one ingress path exists
  - Only FE or only BE exists

  Each ingress path is processed independently.

  If ingress path violates structure rules:
  → STOP with clear error

  ----------------------------------------------------------------------
  ✔ MICRO-FRONTEND BUILD JOB GATING (MANDATORY)
  ----------------------------------------------------------------------
  
  For Micro-Frontend services:
  The agent MUST treat:
   - Build Units = multiple Docker images
   - Runtime Unit = a single Helm release
  
  Build unit rules:
  1. The agent MUST discover ALL micro-frontend build units by inspecting:
   - Repository folder structure
   - Dockerfile stages / arguments
   - Known micro-frontend patterns
  
  2. Each discovered unit MUST have:
   - A dedicated build job
   - A dedicated image name
  
  3. The agent MUST NOT collapse multiple units into a single build job.
  
  Build execution rules (STRICT)
  1. All micro-frontend build jobs MUST be defined statically in the workflow.
  
  2. Build jobs MUST execute conditionally based on:
   - Source code changes (folder-based detection), OR
   - Explicit workflow inputs (e.g. force build all)
  
  3. Default behavior:
     Build ONLY micro-frontends whose source has changed
  
  4. Override behavior:
     A manual input MUST allow forcing ALL builds
  
  5. The agent MUST NOT:
   - Default to building a single primary target
   - Require pipeline regeneration to add or remove build units
  
  Runtime & config rules
  Regardless of the number of micro-frontends:
  - Exactly ONE Helm release
  - Exactly ONE values.yaml
  - Exactly ONE envFrom
  - Shared AppConfig and KeyVault entries
  
  Safety rules
  The agent MUST NOT introduce breaking changes to existing workflows.
  Build selection MUST be achieved via conditions, not pipeline mutation.
