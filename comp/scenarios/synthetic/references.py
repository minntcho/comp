from __future__ import annotations

from comp.compiler_tool import ReferenceCatalog, ReferenceRecord
from comp.scenarios.synthetic.generator import SyntheticInputBundle


def reference_catalog_from_input_bundle(
    input_bundle: SyntheticInputBundle,
) -> ReferenceCatalog:
    return ReferenceCatalog(
        records=tuple(
            ReferenceRecord(
                reference_id=record.reference_id,
                reference_type=record.reference_type,
                labels=(record.label,),
                aliases=("synthetic electricity factor",),
                description=(
                    "Synthetic location-based electricity emission factor for "
                    f"{record.geography} in {record.valid_period}."
                ),
                attributes=(
                    ("concept_id", "pcf.concept.electricity_consumption"),
                    ("geography", record.geography),
                    ("valid_period", record.valid_period),
                    ("method", record.method),
                    ("factor_value", record.factor_value),
                    ("input_unit", record.input_unit),
                    ("output_unit", record.output_unit),
                ),
                source=record.source,
                witness_ids=(record.witness_id,),
            )
            for record in input_bundle.master.reference_catalog
        )
    )


__all__ = ["reference_catalog_from_input_bundle"]
