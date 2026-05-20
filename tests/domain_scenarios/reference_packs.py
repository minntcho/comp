from __future__ import annotations

from dataclasses import dataclass

from comp.compiler_tool import EmbeddingResolverStub, ReferenceCatalog


@dataclass(frozen=True)
class ScenarioReferencePack:
    pack_id: str
    reference_db_version: str
    index_version: str
    catalog: ReferenceCatalog
    resolver: EmbeddingResolverStub


__all__ = ["ScenarioReferencePack"]
