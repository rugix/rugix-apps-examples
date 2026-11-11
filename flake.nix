{
  description = "Native development tools for rugix-apps-examples";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
    in
    {
      devShells = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              skopeo
              jq
              openssh
            ];
          };
          system-tests = pkgs.mkShell {
            packages = with pkgs; [
              qemu
              openssh
            ];
            RUGIX_OVMF_CODE_AMD64 = "${pkgs.OVMF.fd}/FV/OVMF_CODE.fd";
            RUGIX_OVMF_VARS_AMD64 = "${pkgs.OVMF.fd}/FV/OVMF_VARS.fd";
          };
        }
      );
    };
}
