# emit_pass.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from artifacts import ClaimArtifact, CompileArtifacts, PartialFrameArtifact
from comp.views import materialize_public_rows, project_canonical_row
from runtime_env import RuntimeEnv


@dataclass
class EmitPassConfig:
    """
    emit은 committed frame만 대상으로 한다.
    governance에서 merged 여부를 다루므로 여기선 status 변경 안 함.
    """

    emit_only_committed: bool = True
    skip_empty_rows: bool = True
    include_shadow_as_contradiction: bool = True


class EmitPass:
    def __init__(self, config: Optional[EmitPassConfig] = None) -> None:
        self.config = config or EmitPassConfig()

    def run(
        self,
        spec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        claims_by_id = {c.claim_id: c for c in artifacts.claims}
        artifacts.rows = materialize_public_rows(
            artifacts.frames,
            claims_by_id,
            env,
            emit_only_committed=self.config.emit_only_committed,
            skip_empty_rows=self.config.skip_empty_rows,
            include_shadow_as_contradiction=self.config.include_shadow_as_contradiction,
        )
        return artifacts

    def _emit_row(
        self,
        *,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
        env: RuntimeEnv,
    ):
        return project_canonical_row(
            frame=frame,
            claims_by_id=claims_by_id,
            env=env,
            skip_empty_rows=self.config.skip_empty_rows,
            include_shadow_as_contradiction=self.config.include_shadow_as_contradiction,
        )
