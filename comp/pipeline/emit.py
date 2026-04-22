import importlib

_name = "emit" + "_pass"
_legacy = importlib.import_module(_name)
EmitPass = getattr(_legacy, "EmitPass")
EmitPassConfig = getattr(_legacy, "EmitPassConfig")

__all__ = ["EmitPass", "EmitPassConfig"]
