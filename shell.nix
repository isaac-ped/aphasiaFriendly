{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.hello
    pkgs.poetry
    pkgs.python311

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
