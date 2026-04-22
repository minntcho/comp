import importlib

_name = "repair" + "_pass"
_legacy = importlib.import_module(_name)
RepairPass = getattr(_legacy, "RepairPass")
RepairPassConfig = getattr(_legacy, "RepairPassConfig")

__all__ = ["RepairPass", "RepairPassConfig"]
