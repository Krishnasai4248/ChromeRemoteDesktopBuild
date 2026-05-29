---
name: Contextual Update Skill
description: |
  Governs post-scaffolding changes when the user requests modifications
  to specific sections after the initial agent run is complete.
---

  ----------------------------------------------------------------------
  ✔ CONTEXTUAL UPDATE MODE (POST-SCAFFOLDING CHANGES)
  ----------------------------------------------------------------------

  PURPOSE:
  After the initial scaffolding run, the user may request changes to
  specific sections. For example, the user may have said "NO" to
  migrations during the first run, but later decides migrations are
  needed. Or the user may want to update helm values, fix bgm configs,
  change ingress paths, or modify workflow files.

  In these cases, the agent MUST NOT re-run the entire scaffolding.
  Instead, it MUST identify exactly which parts of the EXECUTION ORDER
  apply to the user's request, and execute ONLY those parts - but with
  the SAME rigor and rule compliance as the initial run.

  ----------------------------------------------------------------------
  PROCEDURE (MANDATORY FOR EVERY POST-SCAFFOLDING REQUEST):
  ----------------------------------------------------------------------

  1. RE-READ THE AGENT DEFINITION:
     - The agent MUST read this agent.md file (its own definition)
     - Locate the EXECUTION ORDER step(s) relevant to the user's request
     - Identify ALL rules, constraints, and invariants that apply
       to those steps
     - Map the user's request to specific step numbers
       (e.g., "add migrations" → Steps 17, 27, and related skill rules)

  2. LOAD AND READ ALL SKILLS:
     - The agent MUST load and read the DevOps Pipeline Skill
     - The agent MUST load and read the Helm Runtime Skill
     - Extract all rules relevant to the user's request
     - These skills are located in .polaris/skills/ of the
       target repository
     - The agent MUST follow skill rules with the SAME strictness
       as during the initial run

  3. INSPECT CURRENT STATE:
     - Navigate to the actual files in the target repository
       that are affected by the user's request
     - Read and understand the CURRENT state of those files
     - Understand WHAT was done during the initial run
       (e.g., was migration excluded? what values are in helm?)
     - Identify the GAP between current state and desired state

  4. APPLY CHANGES (EXECUTE THE RELEVANT STEPS):
     - Execute the specific EXECUTION ORDER steps that apply
     - Follow ALL sub-rules within those steps exactly
     - Ensure ALL skill invariants are satisfied
     - Do NOT modify files outside the scope of the request
     - Do NOT re-run the entire scaffolding process
     - If a step requires user input (e.g., migration tool detection),
       ask the user just as the initial run would

  5. VERIFY:
     - After making changes, verify the modified files
       comply with all agent rules and skill constraints
     - Run the FAST MODE RECONCILIATION checks on affected files
     - If any violation is found, fix it immediately

  ----------------------------------------------------------------------
  COMMON SCENARIOS AND STEP MAPPING:
  ----------------------------------------------------------------------

  The following shows which EXECUTION ORDER steps and skill rules
  the agent MUST execute for common post-scaffolding requests:

  SCENARIO: "Add migrations" / "I need migrations now"
  (Database was not detected during initial run, or migrations were excluded)
  Steps to execute:
    → Step 17: Database detection and migration configuration
      * Scan repo for database usage (ORM configs, migration dirs, dependencies)
      * Determine migration tool (scan repo for alembic, manage.py, etc.)
      * Determine workingDir from Mainmanifest.yml file
      * Determine migration command and args
      * If tool cannot be detected → ask the user
    → Step 17 annotation handling:
      * Add Helm hook annotations to azureConfig files:
        - Scan manage-appConfig-secrets/azureConfig/appconfig-*.yml
        <!-- - Scan manage-appConfig-secrets/azureConfig/keyvault-secrets-*.yml -->
      <!-- * Add annotations to configs[], secrets[], containerRegistries[] -->
      * Verify annotations were added successfully
      * If annotations NOT found after processing → ADD them
    → Step 27: Apply migration job to Helm values file
      * Read current helm/{{ .ServiceName }}/values-{{ .ServiceName }}.yml
      * Add the migration job section from the reference template
      * Apply token replacement to the migration section, including {{ .DeploymentName }}
        (resolve from config/MainManifest.yml deployments[].name - typically "api" for backend)
      * {{ .DeploymentName }} appears in envFrom configMapRef and secretRef names in the jobs section
      * Ensure migration workingDir, command, args are set correctly
    → Load DevOps Pipeline Skill for annotation rules
    → Load Helm Runtime Skill for values file structure rules
    → Verify: No remaining tokens (including {{ .DeploymentName }}), valid YAML, annotations present

  SCENARIO: "Update helm values" / "Fix the helm configuration"
  Steps to execute:
    → Step 15: Helm runtime configuration (single envFrom)
    → Step 16: Ingress paths configuration
    → Load Helm Runtime Skill for ALL helm invariants
    → Inspect current values file and identify violations
    → Fix violations while preserving correct existing configuration
    → Verify: Single envFrom, correct ingress, valid structure

  SCENARIO: "Fix bgm config" / "Update release names"
  Steps to execute:
    → Step 18: BGM release name generation
    → Step 19: azureConfig values
    → Load DevOps Pipeline Skill for BGM naming rules
    → Inspect current bgmConfig files
    → Ensure TWO different release names exist
    → Verify: Token replacement complete, valid YAML

  SCENARIO: "Fix workflow files" / "Update docker workflows"
  Steps to execute:
    → Step 9: Reference the FILE COPY whitelist for correct filenames
    → Step 10: Token replacement rules
    → Step 20: Micro-frontend conditional build logic (if applicable)
    → Load DevOps Pipeline Skill for workflow rules
    → Inspect which workflows exist and which are missing/incorrect
    → Fix or regenerate affected workflows only
    → Verify: All 18 workflow files present, tokens replaced

  SCENARIO: "Update MainManifest" / "Add a new service to manifest"
  Steps to execute:
    → Step 10a: MainManifest.yml generation rules
    → Read MainManifest.example.yml and manifest-schema.json
      from the cloned reference repo
    → Inspect current config/MainManifest.yml
    → Make ONLY the requested changes (add service, update infra, etc.)
    → Ensure iamDetails.code remains ServiceName in UPPERCASE, alphabetic only, max 12 chars (Azure Key Vault 24-char limit), globally unique across Aptean products; Key Vault naming: kv-{region}-{lower(iamDetails.code)}-{env}; iamDetails.code = ServiceName.toUpperCase()
    → Validate against manifest-schema.json structure
    → Verify: Valid YAML, schema-compliant

  SCENARIO: "Add/fix annotations" / "Update azureConfig"
  Steps to execute:
    → Step 17 annotation handling (see migration scenario above)
    → Step 19: azureConfig values
    → Load DevOps Pipeline Skill for annotation rules
    → Scan ALL azureConfig and bgmConfig files
    → Add/fix annotations in configs[], secrets[], containerRegistries[]
    → Verify: Annotations present in all required files

  SCENARIO: "Deploy now" / "Trigger pipelines" / "Deploy to dev"
  Steps to execute:
    → Steps 36-42: Deploy phase
    → Load /polaris.deploy command template for PR Auto-Merge Rules,
      Pipeline Trigger Rules, and KeyVault Helm Values Update Rules sections
    → Detect ServiceName from existing workflow files in .github/workflows/
    → Execute deploy sequence: build -> infra -> keyvault -> helm
    → Follow environment progression rules (dev before tst)
    → Track completed steps for retry-from-failure capability

  ----------------------------------------------------------------------
  CRITICAL RULES FOR CONTEXTUAL MODE:
  ----------------------------------------------------------------------
  - The agent MUST NOT guess or rely on memory for rules
  - The agent MUST re-read its own definition for EVERY request
  - The agent MUST load skills fresh for EVERY request
  - The agent MUST inspect actual file contents BEFORE making changes
  - The agent MUST map the user's request to specific EXECUTION ORDER
    steps and execute those steps with full rule compliance
  - If the user's request spans multiple sections, the agent MUST
    read ALL relevant sections and skills
  - The agent MUST NOT skip any sub-rules within a step
    (e.g., if Step 17 says to add annotations, annotations MUST
    be added - not just the migration job)
  - The agent MUST treat each contextual request as if it were
    part of the original execution - same rigor, same validation
  - After changes, the agent MUST commit and create/update the PR
