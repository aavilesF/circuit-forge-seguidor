#!/usr/bin/env bash
# V2 · Genera la electrónica con KiCad 9 (kicad-cli + pcbnew) y Freerouting.
#   hardware/v2/electronica/generar.sh barra        esquemático, PCB enrutada, DRC, paquete de fabricación de la barra
#   hardware/v2/electronica/generar.sh principal    esquemático y ERC de la PCB principal (la PCB se hace en la siguiente entrega)
# Requisitos: KiCad 9 (en el entorno de trabajo, chroot /opt/resolute), Java 21 y freerouting-2.1.0.jar (FREEROUTING=ruta).
set -euo pipefail
cd "$(dirname "$0")"
E=$PWD
RAIZ=$(cd ../../.. && pwd)
K="$RAIZ/hardware/electronics/herramientas/kicad.sh"
# Sin Freerouting: ENRUTAR=0 reutiliza las rutas guardadas en kicad/<proy>/<proy>.ses
FREEROUTING=${FREEROUTING:-$HOME/freerouting-2.1.0.jar}
# El chroot de KiCad 9 necesita ver el repositorio en la misma ruta
if [[ -d /opt/resolute && ! -d /opt/resolute$RAIZ ]]; then mkdir -p /opt/resolute/home/claude; mount --bind /home/claude /opt/resolute/home/claude; fi
if [[ -d /opt/k3d && -d /opt/resolute && ! -d /opt/resolute/opt/k3d/usr ]]; then mkdir -p /opt/resolute/opt/k3d; mount --bind /opt/k3d /opt/resolute/opt/k3d; fi
PY_KICAD=${PY_KICAD:-"chroot /opt/resolute /usr/bin/env HOME=/root python3"}
pcbpy() { $PY_KICAD "$E/generador/pcb.py" "$1" "$E/generador/salida/plan_$2.json"; }

barra() {
  local P=barra_sensores KD="$E/kicad/barra_sensores" VD="$E/verificacion/barra_sensores" FAB="$E/fabricacion/barra_sensores"
  mkdir -p "$VD" "$FAB/gerber"
  echo "== 1. Esquemático y plan";       python3 generador/barra_sensores.py
  echo "== 2. PCB: huellas y DSN";       pcbpy construir $P
  if [[ "${ENRUTAR:-1}" == "1" ]]; then
    echo "== 3. Freerouting"
    (cd "$KD" && timeout 900 java -jar "$FREEROUTING" -de $P.dsn -do $P.ses -mp 40 --gui.enabled=false 2>&1 \
      | grep -v JAVA_TOOL | grep -E '"total_count"|clearance' | head -4 || true)
  fi
  echo "== 4. Rutas, planos de GND, relleno"; pcbpy importar $P; pcbpy rellenar $P; pcbpy pads $P
  echo "== 5. ERC, DRC con paridad, conectividad"
  (cd "$KD" && $K sch erc --format report --severity-all -o "$VD/erc.rpt" $P.kicad_sch >/dev/null \
            && $K pcb drc --format report --severity-all --schematic-parity --all-track-errors -o "$VD/drc.rpt" $P.kicad_pcb >/dev/null \
            && $K pcb drc --format json --severity-all --schematic-parity --all-track-errors -o "$VD/drc.json" $P.kicad_pcb >/dev/null)
  python3 generador/verificar.py barra_sensores
  echo "== 6. Paquete de fabricación"
  (cd "$KD"
   rm -f "$FAB/gerber"/*
   $K pcb export gerbers --no-protel-ext --subtract-soldermask --use-drill-file-origin \
      -l F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts -o "$FAB/gerber/" $P.kicad_pcb >/dev/null
   $K pcb export drill --format excellon --excellon-separate-th --drill-origin plot --excellon-units mm --generate-map --map-format pdf \
      -o "$FAB/gerber/" $P.kicad_pcb >/dev/null
   $K pcb export pos --format csv --units mm --side front --use-drill-file-origin --exclude-dnp -o "$FAB/posiciones_superior.csv" $P.kicad_pcb >/dev/null
   $K pcb export pos --format csv --units mm --side back --use-drill-file-origin --exclude-dnp -o "$FAB/posiciones_inferior.csv" $P.kicad_pcb >/dev/null
   $K pcb export step --subst-models --include-tracks -f -o "$FAB/${P}_pcba.step" $P.kicad_pcb >/dev/null 2>&1 || echo "  (STEP con advertencias)"
   $K pcb export pdf --mode-single -l F.Cu,F.Silkscreen,F.Fab,Edge.Cuts -o "$FAB/${P}_superior.pdf" $P.kicad_pcb >/dev/null
   $K pcb export pdf --mode-single --mirror -l B.Cu,B.Silkscreen,B.Fab,Edge.Cuts -o "$FAB/${P}_inferior.pdf" $P.kicad_pcb >/dev/null
   $K sch export pdf -o "$FAB/${P}_esquematico.pdf" $P.kicad_sch >/dev/null
   for vista in top bottom; do
     $K pcb render --side $vista --quality basic --width 1800 --height 1200 --background opaque \
        -o "$FAB/${P}_3d_${vista}.png" $P.kicad_pcb >/dev/null 2>&1 || echo "  (render $vista no disponible)"
   done)
  (cd "$FAB/gerber" && rm -f ../${P}_gerbers.zip && zip -q ../${P}_gerbers.zip *)
  python3 generador/fabricacion.py barra_sensores
  ls -la "$FAB"
}

principal() {
  local P=principal KD="$E/kicad/principal" VD="$E/verificacion/principal"
  mkdir -p "$VD"
  echo "== 1. Esquemático";   python3 generador/principal.py
  (cd "$KD" && $K sch erc --format report --severity-all -o "$VD/erc.rpt" $P.kicad_sch >/dev/null \
            && $K sch export pdf -o "$E/fabricacion/principal_esquematico.pdf" $P.kicad_sch >/dev/null)
  python3 generador/verificar.py principal
}

mkdir -p "$E/fabricacion"
"${1:-barra}"
