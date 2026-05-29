# Feature Specification: [FEATURE NAME]
*Path: [templates/spec-template.md](templates/spec-template.md)*

<!-- Replace [FEATURE NAME] with the confirmed friendly title generated during /polaris.specify. -->

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Audit & Security *(mandatory)*

<!--
  ACTION REQUIRED: Every feature must answer these four questions before implementation.
  Inherit defaults from the project constitution's "Security & Audit Baseline"
  section (.polaris/memory/constitution.md - Phase 2). If this feature changes
  the data tier, audit policy, AuthN/AuthZ model, or threat surface relative to
  the constitution baseline, document the delta here.
-->

### Data Classification

- **Data tier touched by this feature**: [Public | Internal | Confidential | Restricted]
- **Examples of data in scope**: [list the actual fields, e.g., "user email, organization id, last-login timestamp"]
- **Inherits from constitution baseline**: [Yes / No - if No, justify the delta]

### Audit Logging

- **Events that MUST be logged to the append-only audit trail** (e.g., `audit-trail/<feature>.jsonl` or the configured sink):
  - [event_type] - [trigger] - [fields captured]
  - At minimum, record: actor (principal id), action verb, target (entity + id), timestamp (ISO-8601 UTC), outcome (success / failure / denied), correlation/session id.
- **Retention period**: [e.g., "1 year per constitution baseline"]
- **Sink**: [filesystem audit-trail/, Splunk, Sentinel, S3 + Object Lock, etc.]
- **PII handling**: [redact / hash / store-as-is - state explicitly]

### AuthN / AuthZ

- **Who can invoke this feature**: [public anonymous, authenticated user, role X, role X scoped to own tenant, admin only]
- **Default-deny rule**: [name the policy that gates the feature; if absent, the feature MUST NOT ship]
- **Principal source**: [JWT, header, session, mTLS cert]

### Threat Surface

- **Untrusted input boundaries this feature exposes**: [public HTTP route, webhook, file upload, message queue consumer, scheduled job, SDK call - list each]
- **OWASP Top 10 categories the feature must defend against**: [pick the relevant ones - typically A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A07 ID&A failures]
- **Required mitigations** (link to design decisions in plan.md): [input validation, parameterised queries, rate limiting, output encoding, etc.]
- **Multi-tenant isolation**: [N/A | tenant id scoped via X | single-tenant deployment]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]