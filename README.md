# godot-code-obfuscation

A Python script for obfuscating Godot gdscript code.

## Why create this?

Godot games can be fairly easily exported but that also makes it easy
to extract the contents/assets of a game.  This includes scripts,
images, audio, that type of thing.  For GDScript, this provides
some small amount of protection by providing the following:

* Turn variable names into random characters
* Remove comments
* Remove whitespace and blank lines

This makes it a little harder for people to come along and
make direct changes to an export of your game.  This script
could be utilized as part of a build and release pipeline
for your game such as adding encryption, obfuscating code,
building a binary, and so on.

Note that this does not provide full protection, it only
provides a small deterrence to those who may wish to upload
variants of your game to various platforms.

## Requirements

* Python
* uv

## Setup

```shell
uv sync
```

## Usage

Note that the sript overwrites existing files, *be careful!*
There is no warning or user prompt.  Always use version
control and backups for your projects.

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
