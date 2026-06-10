"""Virgin-boot alias for the validation block.

CB registry id ``validation`` (extended boot / block store) wraps
``ValidationBlock`` — block certification plus a 5-stage item pipeline.

Fork virgin boot registers ``validation_pipeline`` for agent tool calls.
This shim exposes the same registry id without duplicating logic.

See ``docs/validation_block_mapping.md`` for Fork ``ValidationPipelineBlock``
(Pint + empirical_ranges.json) vs CB ``ValidationBlock.validate_pipeline()``.
"""

from app.blocks.validation import ValidationBlock


class ValidationPipelineBlock(ValidationBlock):
    """Fork-compatible registry id; delegates to ValidationBlock."""

    name = "validation_pipeline"
    description = (
        "5-stage validation pipeline — syntactic, dimensional, physical, "
        "empirical, operational checks on structured items"
    )
