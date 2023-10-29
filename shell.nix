{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.poetry
    pkgs.python311
    # A command runner that I like
    # https://github.com/casey/just
    pkgs.just

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
