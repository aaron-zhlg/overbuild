from __future__ import annotations

import ast


class Instrumentor(ast.NodeTransformer):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__()

    def _probe_expr(self, probe_id: str) -> ast.Expr:
        return ast.Expr(
            value=ast.Call(
                func=ast.Name(id="probe_hit", ctx=ast.Load()),
                args=[ast.Constant(probe_id)],
                keywords=[],
            )
        )

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        probe_id = f"func:{self.filename}:{node.name}:{node.lineno}"
        node.body.insert(0, self._probe_expr(probe_id))
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.generic_visit(node)
        probe_id = f"func:{self.filename}:{node.name}:{node.lineno}"
        node.body.insert(0, self._probe_expr(probe_id))
        return node

    def visit_If(self, node: ast.If):
        self.generic_visit(node)

        true_probe = self._probe_expr(
            f"branch:{self.filename}:{node.lineno}:true"
        )
        false_probe = self._probe_expr(
            f"branch:{self.filename}:{node.lineno}:false"
        )

        node.body.insert(0, true_probe)
        if node.orelse:
            node.orelse.insert(0, false_probe)
        else:
            node.orelse = [false_probe]

        return node
