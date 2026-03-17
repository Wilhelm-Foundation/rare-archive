# Contributing to the Rare AI Archive

Thank you for your interest in helping patients with rare diseases. This guide will help you get started.

## Who Can Contribute

- **Clinicians & Geneticists**: Evaluate model outputs, provide preference feedback, validate diagnostic reasoning
- **ML Engineers**: Improve training pipelines, optimize quantization, build evaluation harnesses
- **Bioinformaticians**: Enhance ontology coverage, build tool integrations, curate datasets
- **Software Engineers**: Improve deployment, build infrastructure, enhance the RLHF portal
- **Patient Advocates**: Share perspectives, review clinical tool outputs, help with accessibility

## Getting Started

1. Clone the workspace: `./setup_workspace.sh`
2. Pick a repo that matches your expertise
3. Look for issues labeled `good-first-issue`
4. Read the repo's README and `.agentic/AGENTS.md`

## Development Guidelines

- Follow [Lattice Protocol naming conventions](https://github.com/lattice-protocol): underscores for files, hyphens for HuggingFace-facing names
- All repos use the aDNA triad (`.agentic/what/`, `.agentic/how/`, `.agentic/who/`)
- Write tests for new functionality
- No real patient data (PHI) — synthetic patients only

## Code of Conduct

We are committed to providing a welcoming and inclusive experience. Be kind, be patient, be constructive.
