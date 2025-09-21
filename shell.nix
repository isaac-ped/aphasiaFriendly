{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [

    pkgs.git
    pkgs.flyctl

    pkgs.nodejs-slim # For use in vscode's pylance

    pkgs.redis
    pkgs.docker
    pkgs.buildpack
    pkgs.python312
    pkgs.uv
    # A command runner that I like
    # https://github.com/casey/just
    pkgs.just

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
