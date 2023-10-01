{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.hello
    pkgs.poetry
    pkgs.python311
    pkgs.rustup
    pkgs.cargo
    pkgs.zstd
    pkgs.iconv

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
