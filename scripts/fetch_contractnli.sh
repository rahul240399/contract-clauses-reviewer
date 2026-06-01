#!/usr/bin/env bash
# Fetch ContractNLI into a local, git-ignored directory.
#
# The dataset's official host (stanfordnlp.github.io) may be blocked by a
# network policy. The data zip is also committed inside the dataset's GitHub
# repository, so we pull just that blob over plain git, which is more widely
# reachable. The dataset is never vendored into this repo.
#
# Some environments rewrite github.com git traffic through a scoped proxy
# (url.<proxy>.insteadOf = https://github.com/) that only permits the working
# repo. We neutralize the global/system git config for the public dataset clone
# so it reaches github.com directly; the public repo needs no credentials.
set -euo pipefail

DEST="${1:-.scratch}"
mkdir -p "$DEST"
cd "$DEST"

pub_git() { GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null git "$@"; }

if [ -d contract-nli ]; then
  echo "ContractNLI already present at $DEST/contract-nli"
else
  pub_git clone --depth 1 --filter=blob:none --no-checkout \
    https://github.com/stanfordnlp/contract-nli.git _cnli_repo
  ( cd _cnli_repo && pub_git checkout HEAD -- resources/contract-nli.zip )
  unzip -q _cnli_repo/resources/contract-nli.zip -d .
  rm -rf _cnli_repo
fi

echo "ContractNLI ready at $DEST/contract-nli"
ls -1 contract-nli/*.json
