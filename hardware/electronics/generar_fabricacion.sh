#!/usr/bin/env bash
# Construye la PCB final y el paquete de fabricación del Speed Follower con KiCad 9 (kicad-cli).
# Orden: esquemático -> PCB (colocación + rutas ya calculadas) -> ERC -> DRC con paridad -> conectividad ->
#        (solo si todo pasa) Gerbers, taladros, posiciones, BOM, PDF, STEP y vistas de la PCBA.
# Uso: hardware/electronics/generar_fabricacion.sh            (rutas ya calculadas en generador/rutas.json)
#      hardware/electronics/generar_fabricacion.sh --enrutar  (vuelve a enrutar: ≈ 5-15 min)
set -euo pipefail
cd "$(dirname "$0")"
E=$PWD
K="$E/herramientas/kicad.sh"
# Python con pcbnew de KiCad 9: en el entorno de trabajo está en el chroot /opt/resolute; en una PC con KiCad 9
# instalado basta con PY_KICAD=python3 (Linux) o con el "KiCad 9.0 Command Prompt" (Windows).
PY_KICAD=${PY_KICAD:-"chroot /opt/resolute /usr/bin/env HOME=/root python3"}
pcbnew_py() { $PY_KICAD -c "import os, runpy, sys; os.chdir('$E/generador'); sys.argv=['$1', '${2:-}']; runpy.run_path('$1', run_name='__main__')"; }
FAB="$E/fabricacion"; VER="$E/verificacion"; VISTAS="$E/pcba"
mkdir -p "$FAB/gerber" "$VER" "$VISTAS"

echo "== 1. Esquemático y biblioteca propia"
python3 generador/esquematico.py
(cd kicad && $K sch export netlist --format kicadxml -o "$VER/netlist_esquematico.xml" speed_follower.kicad_sch)
echo "== 2. Plan de la PCB"
python3 generador/pcb_plan.py
python3 generador/modelos3d.py
if [[ "${1:-}" == "--enrutar" ]]; then
  pcbnew_py pcb_kicad.py construir
  (cd generador && python3 enrutar.py 2)
fi
echo "== 3. PCB final (pistas, vías, planos, relleno de zonas, cotas)"
pcbnew_py pcb_kicad.py final
pcbnew_py rellenar_zonas.py              # planos In1 = GND, In2 = +3V3 y rellenos de GND en ambas caras

cd kicad
echo "== 4. ERC"
$K sch erc --format report --severity-all -o "$VER/erc.rpt" speed_follower.kicad_sch
$K sch erc --format json --severity-all -o "$VER/erc.json" speed_follower.kicad_sch >/dev/null
echo "== 5. DRC con paridad esquemático-PCB"
$K pcb drc --format report --severity-all --schematic-parity --all-track-errors -o "$VER/drc.rpt" speed_follower.kicad_pcb
$K pcb drc --format json --severity-all --schematic-parity --all-track-errors -o "$VER/drc.json" speed_follower.kicad_pcb >/dev/null
cd "$E"
echo "== 6. Conectividad diseño = esquemático = PCB"
python3 herramientas/verificar_conectividad.py --pcb
python3 herramientas/resumen_verificacion.py      # falla si ERC o DRC tienen errores sin justificar

cd kicad
echo "== 7. Gerbers, taladros, posiciones"
rm -rf "$FAB/gerber"/*
$K pcb export gerbers --no-protel-ext --subtract-soldermask --use-drill-file-origin \
  -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  -o "$FAB/gerber/" speed_follower.kicad_pcb
$K pcb export drill --format excellon --excellon-separate-th --drill-origin plot --excellon-units mm \
  --generate-map --map-format pdf --generate-report --report-path "$FAB/gerber/speed_follower-taladros.rpt" \
  -o "$FAB/gerber/" speed_follower.kicad_pcb
$K pcb export pos --format csv --units mm --side front --use-drill-file-origin --exclude-dnp \
  -o "$FAB/posiciones_superior.csv" speed_follower.kicad_pcb
$K pcb export pos --format csv --units mm --side back --use-drill-file-origin --exclude-dnp \
  -o "$FAB/posiciones_inferior.csv" speed_follower.kicad_pcb
$K pcb export ipcd356 -o "$FAB/speed_follower.ipc" speed_follower.kicad_pcb
$K pcb export dxf --output-units mm --exclude-refdes --exclude-value --use-drill-origin --mode-single -l Edge.Cuts \
  -o "$FAB/contorno_pcb.dxf" speed_follower.kicad_pcb
(cd "$FAB/gerber" && rm -f ../speed_follower_gerbers.zip && zip -q ../speed_follower_gerbers.zip *)

echo "== 8. PDF: esquemático, capas y planos de ensamblaje"
$K sch export pdf -o "$FAB/esquematico.pdf" speed_follower.kicad_sch
$K pcb export pdf --mode-multipage --ibt -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen --cl Edge.Cuts \
  -o "$FAB/" speed_follower.kicad_pcb
mv -f "$FAB/speed_follower.pdf" "$FAB/pcb_capas.pdf"         # el modo de varias páginas escribe en una carpeta
$K pcb export pdf --mode-single --ibt --sp -l F.Fab,F.Silkscreen,Dwgs.User,Edge.Cuts \
  -o "$FAB/ensamblaje_superior.pdf" speed_follower.kicad_pcb
$K pcb export pdf --mode-single --ibt --sp --mirror -l B.Fab,B.Silkscreen,Dwgs.User,Edge.Cuts \
  -o "$FAB/ensamblaje_inferior.pdf" speed_follower.kicad_pcb
$K pcb export svg --mode-single --fit-page-to-board --exclude-drawing-sheet --sp -l F.Fab,F.Silkscreen,F.Paste,Dwgs.User,Edge.Cuts \
  -o "$VISTAS/pcba_2d_superior.svg" speed_follower.kicad_pcb
$K pcb export svg --mode-single --fit-page-to-board --exclude-drawing-sheet --sp --mirror -l B.Fab,B.Silkscreen,B.Paste,Dwgs.User,Edge.Cuts \
  -o "$VISTAS/pcba_2d_inferior.svg" speed_follower.kicad_pcb

echo "== 9. STEP de la PCBA y vistas 3D"
$K pcb export step --subst-models --include-pads \
  --user-origin 100x100mm -f -o "$FAB/speed_follower_pcba.step" speed_follower.kicad_pcb 2>&1 | tee "$VER/step_export.log"
for v in "top:superior:" "bottom:inferior:" "top:isometrica:-45,0,35"; do
  IFS=: read -r lado nombre giro <<< "$v"
  extra=(); [[ -n "$giro" ]] && extra=(--rotate "$giro" --perspective)
  $K pcb render --side "$lado" --quality high --floor --width 3200 --height 2400 --background opaque "${extra[@]}" \
    -o "$VISTAS/pcba_3d_${nombre}.png" speed_follower.kicad_pcb
done
cd "$E"
python3 ../../herramientas/generar_bom.py
cp ../../docs/BOM_FINAL.csv "$FAB/bom_compra.csv"
python3 herramientas/verificar_modelos3d.py
mkdir -p "$FAB/informes"
cp "$VER/erc.rpt" "$VER/drc.rpt" "$VER/RESUMEN.md" "$VER/modelos3d.md" "$FAB/informes/"
echo "PAQUETE DE FABRICACIÓN LISTO en hardware/electronics/fabricacion/"
