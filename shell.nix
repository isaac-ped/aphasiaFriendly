{ pkgs ? import <nixpkgs> {} }:
let

  imgcat=pkgs.writeShellScriptBin "imgcat" (builtins.readFile ./bin/imgcat);
in

pkgs.mkShell {
  buildInputs = [
    imgcat

    pkgs.flyctl

    pkgs.docker
    pkgs.buildpack
    pkgs.python312
    pkgs.poetry
    # A command runner that I like
    # https://github.com/casey/just
    pkgs.just

    # For svg -> png conversion
    pkgs.imagemagick

    pkgs.pandoc
    pkgs.texlive.combined.scheme-small

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
