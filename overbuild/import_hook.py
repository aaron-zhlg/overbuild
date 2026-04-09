from __future__ import annotations

import ast
import importlib.abc
import os
import sys
from importlib.machinery import PathFinder

from .instrumentor import Instrumentor


def install_import_hook(project_root: str | None = None) -> None:
    root = os.path.abspath(project_root or os.getcwd())
    for finder in sys.meta_path:
        if isinstance(finder, InstrumentFinder) and finder.project_root == root:
            return
    sys.meta_path.insert(0, InstrumentFinder(root))


class InstrumentFinder(importlib.abc.MetaPathFinder):
    def __init__(self, project_root: str) -> None:
        self.project_root = os.path.abspath(project_root)

    def find_spec(self, fullname: str, path=None, target=None):
        spec = PathFinder.find_spec(fullname, path)
        if spec is None or spec.origin is None:
            return None

        filename = os.path.abspath(spec.origin)

        if not filename.endswith(".py"):
            return None
        if not filename.startswith(self.project_root):
            return None

        probe_pkg = os.sep + "overbuild" + os.sep
        if probe_pkg in filename:
            return None

        if "site-packages" in filename or "dist-packages" in filename:
            return None

        spec.loader = InstrumentLoader(filename)
        return spec


class InstrumentLoader(importlib.abc.Loader):
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module) -> None:
        from .runtime import probe_hit

        with open(self.filename, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=self.filename)
        tree = Instrumentor(self.filename).visit(tree)
        ast.fix_missing_locations(tree)

        module.__dict__["probe_hit"] = probe_hit

        code = compile(tree, self.filename, "exec")
        exec(code, module.__dict__)
