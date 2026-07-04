import argparse
from pathlib import Path
# https://github.com/Scony/godot-gdscript-toolkit
from gdtoolkit.parser import parser
from .utils import apply_edits, dump
from .renamer import Renamer
from .stripper import CommentStripper, BlankLineStripper
from .collector import SymbolCollector
from .debugvisitor import DebugVisitor


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


def main():
    args = parse_args()

    input_path = Path(args.input_path)
    excluded_files = set(args.exclude)

    for file_path in input_path.rglob("*.gd"):
        try:
            if file_path.name in excluded_files:
                print(f"Skipping excluded file: {file_path.name}")
                continue

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