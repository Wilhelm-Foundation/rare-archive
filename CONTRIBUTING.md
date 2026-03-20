# Contributing to the Rare AI Archive

Thank you for your interest in helping patients with rare diseases. This guide will help you get started.

## Who Can Contribute

- **Clinicians & Geneticists**: Evaluate model outputs, provide preference feedback, validate diagnostic reasoning
- **ML Engineers**: Improve training pipelines, optimize quantization, build evaluation harnesses
- **Bioinformaticians**: Enhance ontology coverage, build tool integrations, curate datasets
- **Software Engineers**: Improve deployment, build infrastructure, enhance the RLHF portal
- **Patient Advocates**: Share perspectives, review clinical tool outputs, help with accessibility

## Getting Started

1. Clone the repo: `git clone https://github.com/Wilhelm-Foundation/rare-archive.git`
2. Run `./scripts/setup_dev.sh` to install all packages in development mode
3. Pick a package that matches your expertise (see `packages/` directory)
4. Look for issues labeled `good-first-issue`
5. Read the repo's `README.md` and the relevant package README

### Prerequisites

- Python 3.11 or 3.12
- For **training** (`packages/models/`): Linux with NVIDIA GPU, CUDA 12+, PyTorch 2.x
- For **tools** (`packages/tools/`): Internet access for live API testing
- For **deployment** (`deploy/`): Docker Compose v2

## Development Guidelines

- Follow [Lattice Protocol naming conventions](https://github.com/LatticeProtocol): underscores for files, hyphens for HuggingFace-facing names
- Write tests for new functionality
- No real patient data (PHI) — synthetic patients only

## Code of Conduct

We are committed to providing a welcoming and inclusive experience. Be kind, be patient, be constructive.
