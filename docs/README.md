# Documentation

Guides for deploying, evaluating, and extending the Rare AI Archive.

## Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [L1 Local Setup](l1_local_setup.md) | Run the 4B model locally on Apple Silicon with Metal acceleration | Developers, Researchers |
| [Demo Scenarios](demo_scenarios.md) | Clinical demonstration vignettes with expected tool invocations and outputs | Clinicians, Presenters |
| [Demo Video Script](demo_video_script.md) | 4-5 minute screen recording script for stakeholder presentations | Presenters |
| [Evaluation Metrics](evaluation_metrics.md) | How we measure rare disease diagnostic model performance | Researchers, Evaluators |
| [Quantization Guide](quantization_guide.md) | Convert fine-tuned LoRA adapters into deployable GGUF files | ML Engineers |
| [GGUF Quality Verification](gguf_quality_verification.md) | Verify quantized model quality against the full-precision SFT baseline | ML Engineers |
| [Tool Adapter Reference](tool_adapters.md) | Per-tool documentation for all 7 clinical diagnostic tool integrations | Developers |
| [Tool Integration Spec](tool_integration_spec.md) | Architecture and checklist for adding new clinical tools | Developers |
| [User Management](user_management.md) | OpenWebUI account administration and access control | Operators |
| [Troubleshooting](troubleshooting.md) | Common issues and fixes organized by category | All |

## HuggingFace

| Document | Description |
|----------|-------------|
| [HF Org README](hf_org_readme.md) | Draft README for the Wilhelm Foundation HuggingFace organization page |

## Architecture

For system architecture, training pipeline, and deployment topology, see [ARCHITECTURE.md](../ARCHITECTURE.md) in the project root.

---

[Back to main README](../README.md)
