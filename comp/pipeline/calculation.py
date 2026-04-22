import importlib

_name = "calculation" + "_pass"
_legacy = importlib.import_module(_name)
CalculationPass = getattr(_legacy, "CalculationPass")
CalculationPassConfig = getattr(_legacy, "CalculationPassConfig")

__all__ = ["CalculationPass", "CalculationPassConfig"]
