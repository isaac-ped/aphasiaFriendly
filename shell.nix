{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.hello
    pkgs.poetry
    pkgs.python311

    # These are necessary to get pytorch and transformers to work properly
    pkgs.rustup
    pkgs.cargo
    pkgs.zstd
    pkgs.iconv
    pkgs.darwin.apple_sdk.frameworks.Security
    pkgs.pkg-config
    pkgs.openssl

    # keep this line if you use bash
    pkgs.bashInteractive
  ];
}
