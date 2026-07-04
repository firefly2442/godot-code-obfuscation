# https://github.com/Scony/godot-gdscript-toolkit
from gdtoolkit.parser import parser
from gdtoolkit.formatter import format_code
import argparse
from pathlib import Path
import string
import random
from lark import Tree, Token
from dataclasses import dataclass
import re



def parse_args():
    parser = argparse.ArgumentParser(
        description="Obfuscate GDScript (.gd) file or directory contents, renaming identifiers and stripping comments."
    )
    parser.add_argument(
        "input_path",
        help="Path to a .gd file or a directory containing GDScript files."
    )
    parser.add_argument(
        "-e", "--exclude",
        nargs="+",
        default=[],
        metavar="FILE",
        help="One or more filenames to exclude (example: -e UID.gd Player.gd)."
    )

    args = parser.parse_args()

    # Cleanup input path (strip stray quotes, same as original behavior)
    args.input_path = args.input_path.replace("'", "").replace('"', "")

    return args

@dataclass
class Symbol:
    name: str
    token: Token
    kind: str # local, parameter, member, function...
    scope: "Scope"

    new_name: str | None = None

    references: list[Token] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []

class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def define(self, symbol):
        symbol.new_name = generate_name()
        self.symbols[symbol.name] = symbol
        
        # print(f"DEFINE {symbol.kind}: {symbol.name} -> {symbol.new_name}")

    def lookup(self, name):
        scope = self
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None
    

class Visitor:
    def visit(self, node):
        if isinstance(node, Tree):
            method = getattr(self, f"visit_{node.data}", self.generic_visit)
            return method(node)

        elif isinstance(node, Token):
            return self.visit_token(node)

    def visit_token(self, token):
        pass

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)

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

class Renamer(Visitor):
    def __init__(self, global_scope, source):
        self.scope = global_scope
        self.source = source
        self.edits = []

    def visit_func_def(self, node):
        old_scope = self.scope
        self.scope = node.scope
        self.generic_visit(node)
        self.scope = old_scope

    def visit_token(self, token):
        if token.type != "NAME":
            return

        # Don't rename properties after '.'
        if token.start_pos > 0 and self.source[token.start_pos - 1] == ".":
            return

        symbol = self.scope.lookup(token.value)

        if symbol:
            self.edits.append(
                (
                    token.start_pos,
                    token.end_pos,
                    symbol.new_name,
                )
            )

class CommentStripper:
    def __init__(self, source):
        self.source = source
        self.edits = []

    def strip(self):
        src = self.source
        i = 0
        n = len(src)

        in_string = False
        string_char = None
        triple = False

        while i < n:
            c = src[i]

            if not in_string:
                # beginning of string
                if c in ("'", '"'):
                    if src[i:i+3] == c * 3:
                        in_string = True
                        triple = True
                        string_char = c
                        i += 3
                        continue
                    else:
                        in_string = True
                        triple = False
                        string_char = c
                        i += 1
                        continue

                # comment
                if c == "#":
                    start = i

                    while i < n and src[i] != "\n":
                        i += 1

                    self.edits.append((start, i, ""))
                    continue

            else:
                if triple:
                    if src[i:i+3] == string_char * 3:
                        in_string = False
                        triple = False
                        i += 3
                        continue
                else:
                    if c == "\\":
                        i += 2
                        continue

                    if c == string_char:
                        in_string = False
                        i += 1
                        continue

            i += 1

        return apply_edits(src, self.edits)

class BlankLineStripper:
    def __init__(self, source):
        self.source = source

    def strip(self):
        lines = self.source.splitlines()

        # Keep only lines that contain something besides whitespace
        lines = [line for line in lines if line.strip()]

        return "\n".join(lines) + "\n"

class SymbolCollector(Visitor):
    def __init__(self):
        self.global_scope = Scope()
        self.scope = self.global_scope

    def visit_func_def(self, node):
        old_scope = self.scope
        self.scope = Scope(parent=old_scope)

        node.scope = self.scope  # store for renamer

        self.generic_visit(node)

        self.scope = old_scope

    def visit_func_arg_typed(self, node):
        name = node.children[0].value

        self.scope.define(Symbol(
            name=name,
            token=node.children[0],
            kind="param",
            scope=self.scope,
        ))

    def visit_func_var_typed_assgnd(self, node):
        child = node.children[0]

        if isinstance(child, Token) and child.type == "NAME":
            name = child.value

            self.scope.define(Symbol(
                name=name,
                token=child,
                kind="local",
                scope=self.scope,
            ))


def get_name_token(node):
    for child in node.children:
        if isinstance(child, Token) and child.type == "NAME":
            return child
    return None

def generate_name(n=18):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))

def build_rename_map(names, length=18):
    return {name: generate_name(length) for name in names}

def collect_local_variables(tree):
    locals_set = set()

    def walk(node):
        if isinstance(node, Tree):
            if node.data == "func_var_typed_assgnd":
                name_token = node.children[0]
                if isinstance(name_token, Token) and name_token.type == "NAME":
                    locals_set.add(name_token.value)

            for child in node.children:
                walk(child)

    walk(tree)
    return locals_set

def obfuscate_tokens(tree, rename_map):
    def walk(node, in_func_header=False):

        if isinstance(node, Tree):

            if node.data == "func_header":
                in_func_header = True

            for c in node.children:
                walk(c, in_func_header)

        elif isinstance(node, Token):
            # ONLY rename identifiers
            if node.type == "NAME":
                if not in_func_header:
                    if node.value in rename_map:
                        node.value = rename_map[node.value]

        return node

    return walk(tree)


def replace_tokens(node, rename_map):
    if isinstance(node, Tree):
        node.children = [replace_tokens(c, rename_map) for c in node.children]
        return node

    if isinstance(node, Token) and node.type == "NAME":
        if node.value in rename_map:
            return Token(node.type, rename_map[node.value])

    return node

def dump(node, indent=0):
    prefix = "  " * indent

    if isinstance(node, Tree):
        print(f"{prefix}{node.data}")
        for child in node.children:
            dump(child, indent + 1)
    else:
        print(f"{prefix}{node.type}: {node.value}")


def apply_edits(source, edits):
    # sort backwards so offsets stay valid
    edits.sort(key=lambda x: x[0], reverse=True)

    for start, end, replacement in edits:
        source = source[:start] + replacement + source[end:]

    return source

def main():
    args = parse_args()

    input_path = Path(args.input_path)
    excluded_files = set(args.exclude)

    for file_path in input_path.rglob("*.gd"):
        try:
            if file_path.name in excluded_files:
                print(f"Skipping excluded file: {file_path.name}")
                continue

            # if file_path.name != "axis_overlay_node_2d.gd":
            #     continue

            print(f"Processing: {file_path.name}")
            content = file_path.read_text(encoding="utf-8")

            # remove comments
            content = CommentStripper(content).strip()
            # remove empty lines
            content = BlankLineStripper(content).strip()

            tree = parser.parse(content, gather_metadata=True)
            # debug = DebugVisitor()
            # debug.visit(tree)

            # dump(tree)

            collector = SymbolCollector()
            collector.visit(tree)

            renamer = Renamer(collector.global_scope, content)
            renamer.visit(tree)

            new_source = apply_edits(content, renamer.edits)

            # print(new_source)

            file_path.write_text(new_source, encoding="utf-8")
            
            
        except Exception as e:
            print(f"Error reading: {file_path}: {e}")


if __name__ == "__main__":
    main()
