# godot-code-obfuscation

A Python script for obfuscating Godot gdscript code.

## Requirements

* Python
* uv

## Setup

```shell
uv sync
```

## Usage

Note that the sript overwrites existing files, be careful!

```shell
uv run python -m godot_code_obfuscation /path/to/godot-game/
```

This is meant to be run as part of an automated build pipeline.

## Developers

Update `uv.lock` dependencies

```shell
uv lock --upgrade
```

## References

* Supporting Libraries and Links
  * [https://github.com/Scony/godot-gdscript-toolkit](https://github.com/Scony/godot-gdscript-toolkit)
* Alternative Obfuscation Tools
  * [https://github.com/cherriesandmochi/gdmaim](https://github.com/cherriesandmochi/gdmaim)
  * [https://github.com/June-Tree/Godot-Source-Code-Obfuscator](https://github.com/June-Tree/Godot-Source-Code-Obfuscator)
