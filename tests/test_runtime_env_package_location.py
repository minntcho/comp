import runtime_env as legacy
import comp.runtime_env as package


def test_runtime_env_wrapper_matches_package_module():
    assert legacy.LexCandidate is package.LexCandidate
    assert legacy.ScopeFrame is package.ScopeFrame
    assert legacy.ScopePath is package.ScopePath
    assert legacy.ContextEntry is package.ContextEntry
    assert legacy.ContextResolution is package.ContextResolution
    assert legacy.UnitRuntimeInfo is package.UnitRuntimeInfo
    assert legacy.ActivityRuntimeInfo is package.ActivityRuntimeInfo
    assert legacy.SiteRecord is package.SiteRecord
    assert legacy.ContextStore is package.ContextStore
    assert legacy.RuntimeEnv is package.RuntimeEnv
    assert legacy.build_runtime_env is package.build_runtime_env
