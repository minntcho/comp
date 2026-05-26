# Policy-Assembled Trust Kernel

Status: implementation-map
Owner: trust-kernel
Last checked against code: 2026-05-26
Can block PRs: limited

This map describes the intended implementation shape for policy assembly in
`comp`.

It does not freeze public Python APIs, module names, implementation order,
subdocument structure, or final algorithms. It records the shape that future
policy work should preserve while the implementation matures.

The active authority contract remains
`docs/architecture/contracts/policy-boundary.md`. That contract defines what
policy, capability output, scoped grants, and selected validation contracts must
not become. This map explains how those pieces may fit together over time.

## Purpose

The policy boundary is a safety rail. This map is the growth map.

It exists because policy work needs two separate kinds of documentation:

```text
Policy Boundary
  What must never gain validation or public-output authority.

Policy-Assembled Trust Kernel
  How material descriptors, capabilities, effects, grants, ledgers, and selected
  contracts may be assembled before compiler validation.
```

The goal is to keep `comp` flexible without making the authority path soft.
Policy assembly may shape what reaches validation, but compiler validation,
receipt authority, and replay remain separate authority gates.

## View Shift

The old mental model is too small:

```text
input
-> compiler
-> validation
-> output
```

The policy-assembled view is:

```text
external material
-> material descriptor
-> artifact-conditioned capability activation
-> policy effects
-> conflict resolution
-> scoped grants
-> decision ledger
-> selected validation contract
-> compiler validation
-> receipt authority
-> replay verification
```

This shift does not move validation into policy. It makes the pre-validation
boundary explicit so ambiguous, contextual, recommended, or high-risk material
cannot silently enter the compiler path.

## Fixed Process And Assembled Policy

The design separates a stable execution process from profile-specific policy
assembly:

```text
The process kernel is fixed.
Policy assemblies are profile-specific.
Capability activation is artifact-conditioned.
Authority boundaries are invariant.
```

The fixed process keeps audits and tests comparable across profiles. The policy
assembly lets different domains, risk modes, and product contexts choose
different pre-validation behavior without bypassing the same compiler, receipt,
and replay gates.

## Architecture Flow

The intended flow is:

```text
External Material
-> MaterialObservation
-> MaterialDescriptor
-> PolicyProfile / PolicyAssembly
-> CapabilityActivation
-> CandidateSet
-> PolicyEffect IR
-> ConflictResolver
-> SelectionDecision
-> ScopedGrant
-> DecisionLedger
-> SelectedValidationContract
-> ValidationHandoff
-> Compiler Validation
-> PublicOutputReceipt
-> Replay
```

The stages before `ValidationHandoff` may classify, propose, hold, reject,
scope, or record material. They do not validate claims.

The stages after `ValidationHandoff` remain the existing trust path. Compiler
validation decides whether compiler-facing material satisfies selected
requirements. `PublicOutputReceipt` remains the only public projection
authority. Replay verifies the receipt path.

## Policy Families

Policy work should start with a small core and expand only when code, tests, or
downstream pressure needs the distinction.

Core policy families:

```text
ActivationPolicy
  Decides which capabilities may run for the described material.

SelectionPolicy
  Decides whether candidate material is selected, proposed, held, or rejected.

ScopePolicy
  Decides which pipeline scopes selected or unselected material may enter.

RetentionPolicy
  Decides how long policy, decision, and replay-support material should be kept.

AuthorityBoundaryPolicy
  Preserves non-overridable rules from policy-boundary.md.
```

Future policy families:

```text
IngressPolicy
DescriptorPolicy
ResolutionPolicy
EvidencePolicy
RiskPolicy
EscalationPolicy
PromotionPolicy
ShadowPolicy
MetaPolicy
```

Future families should not be added just to make the taxonomy complete. Add one
when it prevents authority confusion, removes real duplication, or lets two
profiles differ without changing the compiler authority path.

## Artifact-Conditioned Activation

Capability activation should be driven by the material descriptor and active
profile, not by a fixed "always run every resolver" pipeline.

Examples:

```text
declared_alias + low risk
-> declared resolver only
-> embedding off
-> LLM off

unknown + medium risk + source context
-> embedding candidate retrieval
-> LLM recommendation may be enabled
-> reviewer escalation may stay conditional

high-risk + public_possible
-> auto-select disabled
-> evidence or reviewer policy required

non_public material
-> projection_candidate denied
-> validation_context may still be allowed if policy permits it
```

This keeps retrieval, embeddings, LLMs, reviewers, and evidence requests as
capabilities. They may produce candidate or recommendation material, but the
policy boundary decides whether that material may cross into later scopes.

## ScopedGrant Lifecycle

Selection status alone is insufficient.

A material or decision needs the proper scoped grant before it can cross a
pipeline boundary:

```text
selected
+ validation_handoff grant
+ selected validation contract
-> compiler input may be constructed
```

But:

```text
selected != validated
validated != public authority
projection_candidate != public projection
PublicOutputReceipt == public projection authority
```

Initial scope vocabulary:

```text
candidate_generation
selection_evaluation
validation_context
validation_handoff
projection_candidate
replay_support
audit_only
```

`ScopedGrant` is pipeline access, not trust authority. A grant may explain why
material may be used in a stage, but it must not make a claim checked, close a
validation requirement, authorize public projection, or replace replay.

## Decision Ledger

`DecisionLedger` is the audit spine for policy assembly.

It explains why material crossed or did not cross a boundary. Useful ledger
entries may include:

```text
material descriptor
activated capabilities
candidate set
policy effects
conflict resolution result
selection decisions
scoped grants
denied scopes
retention class
selected validation contract digest
policy artifact digest
policy profile id
policy assembly version
```

The ledger is explanation and audit material. It is not authority by itself.
Its digest is an audit identifier, not a receipt, replay proof, or validation
result.
Its value is that future replay, review, debugging, shadow-policy comparison,
or counterfactual analysis can see why a run shaped validation input the way it
did.

## Selected Validation Contract

`SelectedValidationContract` freezes what the compiler is allowed to see for a
run.

It may include:

```text
active fields
active mappings
active units
active rules
validation scope
selected decision target snapshot
projection candidate scope
decision ledger digest
policy profile id
contract version
```

The selected validation contract is compiler-facing input shape, not validation
authority. When it carries selected decision target snapshots,
`ValidationHandoff` must bind each handoff claim field to the frozen target
before producing compiler input.

The key distinction remains:

```text
selected for validation != selected for projection
```

Projection requires the existing commit, receipt, and replay path. A selected
contract can explain what the compiler checked; it cannot publish anything.

## Authority Roles

The assembled architecture should keep these roles separate:

```text
PolicyEffect
  Decision material.

ConflictResolver
  Composition step from effects to decisions and scoped grants.

PolicyAssembly
  Ledger and selected-contract assembly step from descriptors, effects, and
  decision subjects.

ScopedGrant
  Pipeline access.

SelectedValidationContract
  Compiler-facing contract.

ValidationHandoff
  Runtime bridge from selected contract to compiler input.

ValidationReport
  Compiler judgment.

ReviewPackage / ReviewDecision
  Commit-readiness and governance material, not public-output authority.

PublicOutputReceipt
  Public projection authority.

Replay
  Verification of the receipt path.
```

If a future PR blurs these roles, the policy-boundary active contract should
block it. If a future PR implements these roles with different names but keeps
the authority split intact, this map should be updated rather than treated as a
name lockfile.

## Implementation Slices

The implementation should advance in small, reviewable slices:

```text
Slice 1: Boundary contract
  Add and maintain policy-boundary.md as the active safety rail.

Slice 2: Descriptor and effect vocabulary
  Introduce minimal MaterialDescriptor and PolicyEffect shapes where code needs
  them. Keep outputs non-authoritative.

Slice 3: Conflict resolver, policy assembly, selection decision, scoped grant, and ledger
  Record selected/proposed/held/rejected outcomes with pipeline scopes and
  decision basis.

Slice 4: Selected validation contract and validation handoff
  Freeze what the compiler may see for a run without moving validation into
  policy code.

Slice 5: Retention, shadow policy, and counterfactual replay support
  Preserve enough policy-decision material to compare policy behavior without
  changing receipt authority.
```

Each slice should come with tests that protect the authority boundary it
touches. If a slice needs a stronger invariant than this map provides, promote
that invariant into an active contract or extend `policy-boundary.md`.

## Current Implementation Status

This map describes intended architecture shape, not a completed implementation.

The current codebase already has precursor surfaces:

```text
comp.policy.MaterialDescriptor
comp.policy.PolicyEffect
comp.policy.ConflictResolver
comp.policy.PolicyAssembly
comp.policy.ScopedGrant
comp.policy.SelectionDecision
comp.policy.DecisionLedger
comp.policy.SelectedValidationContract
comp.policy.policy_artifact_digest
comp.runtime.ValidationHandoff
CompilerProfile
DomainPack
RetrievalQueryPolicy
ReferenceOption
CanonicalReference
ValidationReport
PublicOutputReceipt
replay_public_projection(...)
```

`comp.policy.MaterialDescriptor`, `PolicyEffect`, `ConflictResolver`,
`PolicyAssembly`, `ScopedGrant`, `SelectionDecision`, `DecisionLedger`, and
`SelectedValidationContract` are the first minimal vocabulary slices. They
describe pre-validation material, policy effects, effect composition, ledger
and selected-contract assembly, scoped pipeline access, selection status,
decision audit records, stable policy artifact digests, and the
compiler-facing contract shape. They do not validate claims, authorize
projection, or replay receipts. A selected decision still requires a
`validation_handoff` grant before it can be included in a selected validation
contract, and that contract remains pre-validation.

`comp.runtime.ValidationHandoff` is the first bridge from selected validation
contract to compiler-facing `InterpretationHypothesis`. It only carries
contract-selected claims and witnesses across the handoff boundary. It has no
`CompilerTool`, commit, receipt, projection, or replay authority.

The other surfaces show the existing authority direction: profiles declare
behavior, retrieval produces candidates, deterministic selectors bind
references, compiler validation judges claims, receipts authorize projection,
and replay verifies the receipt path.

Future policy work should connect to that direction instead of introducing a
parallel source of selection truth, validation truth, receipt truth, or
projection truth.

## Non-Goals

This map does not prescribe:

```text
public API names
class names
module names
package layout
database schema
implementation order beyond rough slices
exact policy taxonomy
final conflict-resolution algorithm
```

Those details should be introduced only when an implementation slice needs them
and can test the authority boundary they affect.
