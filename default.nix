argsOuter@{...}:
let
  # specifying args defaults in this slightly non-standard way to allow us to include the default values in `args`
  args = rec {
    pkgs = import <nixpkgs> {};
    pythonPackages = pkgs.python36Packages;
    forDev = true;
    localOverridesPath = ./local.nix;
  } // argsOuter;
in (with args; {
  digitalMarketplaceSupplierFrontendEnv = (pkgs.stdenv.mkDerivation rec {
    name = "digitalmarketplace-supplier-frontend-env";
    shortName = "dm-sup-fe";
    buildInputs = [
      pythonPackages.python
      pkgs.nodejs-8_x
      pkgs.yarn
      pkgs.libffi
      pkgs.libyaml
      # pip requires git to fetch some of its dependencies
      pkgs.git
      # for `cryptography`
      pkgs.openssl
      pkgs.cacert
    ] ++ pkgs.stdenv.lib.optionals forDev ([
        # for lxml
        pkgs.libxml2
        pkgs.libxslt
        # for frontend tests
        pkgs.phantomjs
      ] ++ pkgs.stdenv.lib.optionals pkgs.stdenv.isDarwin [
        # for watchdog... not that it works on darwin yet anyway, but it will/would need them
        pkgs.darwin.apple_sdk.frameworks.CoreServices
        pkgs.darwin.cf-private
      ]
    );

    hardeningDisable = pkgs.stdenv.lib.optionals pkgs.stdenv.isDarwin [ "format" ];

    GIT_SSL_CAINFO="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
    VIRTUALENV_ROOT = (toString (./.)) + "/venv${pythonPackages.python.pythonVersion}";
    VIRTUAL_ENV_DISABLE_PROMPT = "1";
    SOURCE_DATE_EPOCH = "315532800";

    # if we don't have this, we get unicode troubles in a --pure nix-shell
    LANG="en_GB.UTF-8";

    shellHook = ''
      export PS1="\[\e[0;36m\](nix-shell\[\e[0m\]:\[\e[0;36m\]${shortName})\[\e[0;32m\]\u@\h\[\e[0m\]:\[\e[0m\]\[\e[0;36m\]\w\[\e[0m\]\$ "

      if [ ! -e $VIRTUALENV_ROOT ]; then
        ${pythonPackages.python}/bin/python -m venv $VIRTUALENV_ROOT
      fi
      source $VIRTUALENV_ROOT/bin/activate
      make -C ${toString (./.)} requirements${pkgs.stdenv.lib.optionalString forDev "-dev"}
    '';
  }).overrideAttrs (if builtins.pathExists localOverridesPath then (import localOverridesPath args) else (x: x));
})
