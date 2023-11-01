{ pkgs ? import <nixpkgs> {} }:
let

  imgcat=pkgs.writeShellScriptBin "imgcat" (builtins.readFile ./bin/imgcat);
in

pkgs.mkShell {
  buildInputs = [
    imgcat
    pkgs.poetry
    pkgs.python311
    # A command runner that I like
    # https://github.com/casey/just
    pkgs.just

    # For svg -> png conversion
    pkgs.imagemagick

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
