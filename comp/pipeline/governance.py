import importlib

_name = "governance" + "_pass"
_legacy = importlib.import_module(_name)
GovernancePass = getattr(_legacy, "GovernancePass")
GovernancePassConfig = getattr(_legacy, "GovernancePassConfig")

__all__ = ["GovernancePass", "GovernancePassConfig"]
