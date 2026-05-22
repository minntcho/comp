# Compiler / Domain Boundary

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-22
Can block PRs: yes

This contract consolidates the compiler/domain boundary already described by
`trust-kernel-extension-rings.md`, `trust-kernel-hardening.md`, and
`extension-port-contracts.md`.

The governing rule is:

```text
Core code must own protocol, not domain meaning.
Domain behavior may be declared and fingerprinted, but it does not become
authority.
```

## Core Compiler Owns

The core compiler owns lifecycle and authority transitions:

```text
claim lifecycle
requirement lifecycle
witness grounding protocol
semantic judgment protocol validation
ReferenceOption -> CanonicalReference promotion
calculation trace minimum contract
review package construction
receipt build conditions
public projection gate
```

The core may reject incomplete, ungrounded, conflicting, or unsupported
submitted artifacts. It must not infer ESG, LCA, DPP, PCF, supplier-workflow, or
product-passport meaning from those artifacts.

## Domain Declaration Surfaces Own

Domain declaration surfaces describe behavior that the compiler may validate,
activate, fingerprint, and cite:

```text
domain fields
allowed units
domain rule families
semantic rubrics
judge policies
reference catalogs
calculation formulas
retrieval query policies
projection field sets
```

These surfaces are declarations, not authority overrides. A declaration can make
the compiler stricter, open more requirements, or supply domain-specific
material for deterministic gates. It must not bypass those gates.

## DomainPack And CompilerProfile

DomainPack is a declaration library.
CompilerProfile is the active behavior lock.
Neither is authority.

`DomainPack` may declare domain behavior such as fields, allowed units, rule
families, semantic rubrics, judge policies, and retrieval query policies.
Installed domain packs are inactive until a profile activates their declarations.

`CompilerProfile` may activate and fingerprint behavior. It locks the active
rule ids, rubric ids, retrieval policy ids, judge policy, projection policy, core
invariant version, and domain-pack declaration fingerprints used for a compiler
run.

The compiler still owns protocol validation, authority promotion, and
receipt-gated projection.

## Structural Field Policy

Core may know structural claim fields only when they are part of the compiler
baseline protocol.

`unit` is currently treated as a structural claim field because unit presence and
allowed-unit membership are cross-domain compiler safety checks. The allowed
unit set remains profile-declared behavior. The domain meaning of a unit remains
domain-owned.

Allowed in core:

```text
detect that a submitted claim has a unit field
detect that a required structural unit field is missing
check that a submitted unit value is in profile-declared allowed_units
```

Forbidden in core:

```text
infer that kWh means Scope 2
infer that kgCO2e means PCF
decide factor compatibility from unit meaning alone
map a unit to ESG, LCA, DPP, supplier, or product-passport semantics
```

## Import Boundary

Core authority modules must not import concrete domain, product, scenario, runtime, or agent packages.
This is machine-checked by
`tests/test_authority_import_boundaries.py`.

The allowed direction is:

```text
domain/profile declarations -> compiler contracts
outer adapters and agents -> compiler contracts
compiler authority path -/-> concrete domain, product, scenario, runtime, or
agent packages
```

## Forbidden

These actions violate the boundary:

```text
hardcoding ESG, LCA, DPP, PCF, supplier, or product-passport business meaning in
core compiler modules
letting a DomainPack mint PublicOutputReceipt
letting a CompilerProfile disable core invariants
letting a rule evaluator bypass compiler validation
letting ReferenceCatalog become projection authority
letting CalculationFormula output become public output without receipt
letting public projection run without PublicOutputReceipt
```

Review question:

```text
Does this change keep domain meaning declarative while leaving lifecycle,
authority promotion, and receipt-gated projection inside deterministic compiler
gates?
```
