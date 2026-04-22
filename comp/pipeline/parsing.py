import importlib

_name = "parse" + "_pass"
_legacy = importlib.import_module(_name)
ParsePass = getattr(_legacy, "ParsePass")

__all__ = ["ParsePass"]
