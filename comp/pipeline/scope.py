import importlib

_name = "scope" + "_resolution" + "_pass"
_legacy = importlib.import_module(_name)
ScopeResolutionPass = getattr(_legacy, "ScopeResolutionPass")

__all__ = ["ScopeResolutionPass"]
