#!/usr/bin/env bash
# Ejecuta kicad-cli 9. En el entorno de trabajo KiCad 9.0.8 está en un chroot de Ubuntu 26.04 (/opt/resolute);
# en Windows/Linux con KiCad 9 instalado se usa el kicad-cli del sistema.
if command -v kicad-cli >/dev/null 2>&1 && kicad-cli version 2>/dev/null | grep -q '^9\.'; then exec kicad-cli "$@"; fi
exec chroot /opt/resolute /usr/bin/env HOME=/root KICAD9_3DMODEL_DIR=/opt/k3d/usr/share/kicad/3dmodels \
  bash -c 'cd "$0" && exec kicad-cli "$@"' "$PWD" "$@"
