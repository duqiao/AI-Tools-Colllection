# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI Tools Collection** repository that uses the **Specify** framework for structured development. The repository is currently empty of actual source code but contains a comprehensive development workflow infrastructure.

## Development Workflow

This project uses a specification-first development approach with the following key components:

### Feature Creation Workflow
- **Create new feature**: `.specify/scripts/powershell/create-new-feature.ps1 <feature description>`
  - Generates numbered feature branches (format: `001-feature-name`)
  - Creates specification directory under `specs/`
  - Copies spec template from `.specify/templates/spec-template.md`
  - Sets `SPECIFY_FEATURE` environment variable

- **Setup implementation plan**: `.specify/scripts/powershell/setup-plan.ps1`
  - Creates implementation plan from `.specify/templates/plan-template.md`
  - Validates proper feature branch naming (git repos only)

### Directory Structure
```
/
├── .specify/
│   ├── memory/
│   │   └── constitution.md          # Project constitution and principles
│   ├── templates/                   # Document templates
│   │   ├── spec-template.md         # Feature specification template
│   │   ├── plan-template.md         # Implementation plan template
│   │   ├── checklist-template.md    # Testing checklist template
│   │   ├── tasks-template.md        # Task breakdown template
│   │   └── agent-file-template.md   # Agent context template
│   └── scripts/
│       └── powershell/              # PowerShell automation scripts
│           ├── create-new-feature.ps1
│           ├── setup-plan.ps1
│           ├── common.ps1
│           └── update-agent-context.ps1
├── specs/                           # Feature specifications (auto-generated)
│   └── XXX-feature-name/
│       ├── spec.md                  # Feature specification
│       ├── plan.md                  # Implementation plan
│       ├── tasks.md                 # Task breakdown
│       ├── research.md              # Research findings
│       ├── data-model.md            # Data model design
│       ├── quickstart.md            # Quick start guide
│       └── contracts/               # API contracts
└── .claude/
    ├── commands/                    # Claude Code slash commands
    │   ├── speckit.plan.md         # Planning workflow
    │   ├── speckit.implement.md    # Implementation workflow
    │   ├── speckit.analyze.md      # Analysis workflow
    │   └── speckit.*.md            # Other workflow commands
    └── settings.local.json         # Claude Code settings
```

## Claude Code Commands

The repository includes custom slash commands for the Specify workflow:

- `/speckit plan` - Execute implementation planning workflow
- `/speckit implement` - Execute implementation workflow  
- `/speckit analyze` - Execute analysis workflow
- `/speckit tasks` - Generate task breakdown
- `/speckit checklist` - Generate testing checklist
- `/speckit clarify` - Clarify requirements
- `/speckit constitution` - View project constitution

## Key Principles

Based on the constitution template, this project follows:

1. **Library-First Approach**: Every feature starts as a standalone library
2. **CLI Interface**: All functionality exposed via command-line interfaces
3. **Test-First Development**: TDD mandatory with Red-Green-Refactor cycle
4. **Integration Testing**: Focus on contract testing and inter-service communication
5. **Text I/O Protocol**: stdin/args → stdout, errors → stderr with JSON + human-readable formats

## Environment Variables

- `SPECIFY_FEATURE`: Current feature name/branch (set automatically by feature creation script)

## Development Notes

- Repository supports both git and non-git workflows
- PowerShell scripts provide cross-platform compatibility
- All feature branches follow numbered naming convention (XXX-description)
- Templates ensure consistent documentation and planning
- Agent context files are updated automatically during planning phases

## Getting Started

1. Create a new feature: `.specify/scripts/powershell/create-new-feature.ps1 "Your feature description"`
2. Plan the implementation: `/speckit plan`
3. Implement the feature: `/speckit implement`