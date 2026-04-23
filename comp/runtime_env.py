import importlib

_name = "runtime" + "_env"
_legacy = importlib.import_module(_name)
RuntimeEnv = getattr(_legacy, "RuntimeEnv")
LexCandidate = getattr(_legacy, "LexCandidate")
ScopePath = getattr(_legacy, "ScopePath")
SiteRecord = getattr(_legacy, "SiteRecord")
build_runtime_env = getattr(_legacy, "build_runtime_env")

__all__ = ["RuntimeEnv", "LexCandidate", "ScopePath", "SiteRecord", "build_runtime_env"]
