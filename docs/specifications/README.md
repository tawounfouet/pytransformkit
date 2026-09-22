# PyTransformKit Specifications

This directory contains the numbered functional and architectural specifications that define PyTransformKit.

Implementation should follow these specifications while allowing evidence from real code and tests to refine provisional design decisions.

The first implementation is driven by:

- repository bootstrap;
- shared kernel;
- logical data type and schema model;
- Dataset domain model;
- Expression AST;
- Select / Filter / Derive transformations;
- Pipeline and LogicalPlan.


## Frozen implementation roadmap

The normative path from the completed first multi-engine cycle to the stable release
is defined in:

- `../ROADMAP_LOT_11_TO_1_0.md`

This roadmap freezes `LOT-11` through `LOT-28`, with `LOT-28` producing
PyTransformKit `1.0.0`.
