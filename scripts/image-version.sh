#!/usr/bin/env sh
#
# Classe:
#    image-version.sh
# Descrição:
#    Classe de configuração
# Autor:
#    Euríval
# Data:
#    2026-01-13
# Arquivo:
#    image-version.sh
# Função:
#    Classe de configuração
# Importações:
#    from __future__ import annotations
#    import os
#    from dataclasses import dataclass

set -eu

SHA="${GITHUB_SHA:-$(git rev-parse --verify HEAD)}"
SHORT_SHA=$(printf '%s' "$SHA" | cut -c1-7)
STAMP=$(date -u +%Y%m%d.%H%M%S)

printf '%s-%s\n' "$STAMP" "$SHORT_SHA"
