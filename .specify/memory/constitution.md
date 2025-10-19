<!--
Sync Impact Report:
- Version change: 0.0.0 → 1.0.0 (initial constitution creation)
- Added sections: Core Principles, Development Workflow, Technology Standards, Governance
- Templates requiring updates: ✅ All templates reviewed and aligned
- Follow-up TODOs: None
-->

# AI Tools Collection Constitution

## Core Principles

### I. Library-First Architecture
Every AI tool starts as a standalone library with clear, single responsibility. Libraries must be self-contained, independently testable, fully documented, and composable. No organizational-only libraries - each must provide demonstrable user value on its own.

### II. CLI Interface Standard
All libraries expose functionality via command-line interfaces following text I/O protocol: stdin/args → stdout, errors → stderr. Each tool MUST support both JSON (for machine parsing) and human-readable formats (for direct usage). CLI is the primary user interface.

### III. Test-First Development (NON-NEGOTIABLE)
Test-Driven Development is mandatory: Tests written first → User reviews and approves → Tests must fail → Only then implement. Red-Green-Refactor cycle strictly enforced with no exceptions. Unit tests for individual components, integration tests for workflows.

### IV. Specification-First Workflow
No code implementation without prior specification. Every feature MUST follow the Specify workflow: create feature → plan → research → design → implement. Specifications are living documents that guide implementation and serve as acceptance criteria.

### V. Cross-Platform Compatibility
All tools MUST work across major platforms (Windows, macOS, Linux). Use cross-platform technologies and avoid platform-specific locking. PowerShell scripts provide cross-platform automation. Dependencies must be platform-agnostic.

## Development Workflow

### Feature Lifecycle
1. **Specification**: User requirements captured using `.specify/scripts/powershell/create-new-feature.ps1`
2. **Planning**: Technical approach designed using `/speckit.plan` command
3. **Research**: Unknowns resolved and decisions documented
4. **Design**: Data models, contracts, and quickstart guides created
5. **Implementation**: Code written following test-first principles
6. **Validation**: Independent testing of each user story

### Branch Management
- Feature branches follow numbered naming: `XXX-feature-description`
- Each feature has dedicated specification directory under `specs/`
- Features must be independently testable and deployable
- Git integration optional but recommended

## Technology Standards

### Language and Framework Selection
- Primary languages: Python, TypeScript/JavaScript, PowerShell
- Framework choice justified by research phase
- All dependencies explicitly documented in plan.md
- Prefer batteries-included, mature frameworks

### Documentation Requirements
- Every tool includes comprehensive README
- CLI help built-in (`--help` flag)
- API documentation generated from contracts
- Quickstart guide for each feature

### Testing Standards
- Unit tests for core logic
- Integration tests for CLI workflows
- Contract tests for API boundaries
- Performance benchmarks for AI tools

## Governance

### Amendment Process
- Constitution supersedes all other practices and templates
- Amendments require documented justification and version increment
- Changes must maintain backward compatibility or include migration plan
- All templates and commands must be updated to reflect constitution changes

### Compliance Review
- All implementation plans must pass Constitution Check gates
- Complexity violations must be explicitly justified with simpler alternatives considered
- Template updates required when constitution principles change
- Regular review of template alignment with constitution

### Version Policy
Constitution follows semantic versioning:
- **MAJOR**: Backward incompatible governance changes or principle removals
- **MINOR**: New principles/sections added or material guidance expansions  
- **PATCH**: Clarifications, wording fixes, non-semantic refinements

### Quality Gates
- No code without prior specification and plan approval
- All tests must pass before feature completion
- Each user story independently verifiable
- Documentation completeness required for release

**Version**: 1.0.0 | **Ratified**: 2025-10-18 | **Last Amended**: 2025-10-18