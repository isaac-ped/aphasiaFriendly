# Readable AF

Creating aphasia friendly communication from complicated texts.

## Installation

This repository is set up for dependency management with [nix](https://nixos.org/)

Follow the instructions on that site or use the quick command:

```shell
sh <(curl -L https://nixos.org/nix/install) --daemon
```
to install nix, then run

```
nix-shell
```

from this directory to enter a shell with all dependencies installed.

## Usage

Use the shortcut script:

```bash
./af
```

to install dependencies and access possible commands:

```bash
Usage: af [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  summarize         Create an aphasia-friendly summary
```
