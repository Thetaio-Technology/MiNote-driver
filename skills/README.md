# Skills

This directory holds reusable skill definitions built on top of the local MiNote automation framework.

Currently available:

- `minote-todo`: exposes the verified Xiaomi Cloud Notes todo automation as a reusable skill backend.

The intent of this directory is to package the existing low-level framework into skill-oriented documentation and entrypoints without introducing a natural-language parser.

Recommended files inside a skill package:

- `SKILL.md`: high-level purpose, scope, and operating rules
- `interface.md`: input and output contract
- `examples.md`: example mappings and calls
- `checklist.md`: execution and verification checklist
