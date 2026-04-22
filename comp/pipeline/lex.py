import importlib

_legacy = importlib.import_module("lex_pass")
LexPass = _legacy.LexPass

__all__ = ["LexPass"]
