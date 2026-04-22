import importlib

_name = "runtime" + "_env"
_legacy = importlib.import_module(_name)
RuntimeEnv = getattr(_legacy, "RuntimeEnv")
build_runtime_env = getattr(_legacy, "build_runtime_env")

__all__ = ["RuntimeEnv", "build_runtime_env"]
