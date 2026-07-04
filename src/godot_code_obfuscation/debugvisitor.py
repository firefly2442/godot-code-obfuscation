from lark import Tree, Token
from .visitor import Visitor


class DebugVisitor(Visitor):
    WATCH = {
        "func_def",
        "func_header",
        "func_arg",
        "func_arg_typed",
        "func_var_assgnd",
        "func_var_typed_assgnd",
        "var_stmt",
    }

    def generic_visit(self, node):
        if node.data in self.WATCH:
            print(f"\n=== {node.data} ===")

            for i, child in enumerate(node.children):
                if isinstance(child, Tree):
                    print(f"  [{i}] Tree({child.data})")
                else:
                    print(f"  [{i}] Token({child.type}, {child.value})")

        super().generic_visit(node)
