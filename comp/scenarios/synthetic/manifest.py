from __future__ import annotations

import hashlib
import json
from typing import Any

from comp.scenarios.synthetic.config import SyntheticScenarioConfig


def build_config_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_manifest(
    config: SyntheticScenarioConfig,
    *,
    output_contract: tuple[str, ...],
) -> dict[str, Any]:
    payload = config.manifest_payload()
    return {
        "generator": "comp.scenarios.synthetic",
        "scenario_id": config.scenario_id,
        "phase": "synthetic_scenario_v1",
        "output_contract": output_contract,
        "authority": "oracle_for_tests_only",
        "non_authority_notice": (
            "Synthetic oracle files are test expectations. CommitReceipt remains "
            "the only public projection authority."
        ),
        "reproducibility": {
            "seed": config.seed,
            "profile_id": config.profile_id,
            "config_hash": build_config_hash(payload),
        },
        "config": payload,
        "sources": [
            {
                "source_ref": "reference_catalog.csv",
                "role": "master_reference_catalog",
                "path": "master/reference_catalog.csv",
                "media_type": "text/csv",
                "schema_id": "synthetic.master_reference_catalog.v1",
            },
            {
                "source_ref": "sites.csv",
                "role": "master_sites",
                "path": "master/sites.csv",
                "media_type": "text/csv",
                "schema_id": "synthetic.master_sites.v1",
            },
            {
                "source_ref": "products.csv",
                "role": "master_products",
                "path": "master/products.csv",
                "media_type": "text/csv",
                "schema_id": "synthetic.master_products.v1",
            },
            {
                "source_ref": config.source_ref,
                "role": "raw_source",
                "path": f"raw_sources/{config.source_ref}",
                "media_type": "text/csv",
                "schema_id": "synthetic.erp_electricity.v1",
            },
        ],
    }


__all__ = ["build_config_hash", "build_manifest"]
