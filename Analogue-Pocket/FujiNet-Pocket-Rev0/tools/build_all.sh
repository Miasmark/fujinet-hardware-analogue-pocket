#!/usr/bin/env bash
# Regenerate FujiNet Pocket Rev0 (DRAFT): the footprints, the schematic (root + 4 sheets, with
# sch_draw's connectivity check, the hierarchy check and netlist parity against design.py), ERC at
# every severity, the firmware pin-map check, the BOM and the schematic PDF; with LAYOUT=1 also the
# board (placement, routing, DRC with schematic parity) and its fab / shell outputs.  Needs KiCad 10
# and Python 3; the board also KiCad's pcbnew Python module (PCBNEW_PYTHON, default /usr/bin/python3),
# numpy, and Freerouting 2.4.1 on Java 25 (JAVA).  tools/harvest_symbols.py refreshes tools/symcache.sexpr from the installed KiCad
# libraries; run it only when design.py takes a new stock symbol.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
python3 tools/make_edge_fp.py >/dev/null      # the Pocket / GB edge footprint
python3 tools/make_fp_extra.py >/dev/null     # the LiPo landing pad
python3 tools/make_cell_step.py >/dev/null    # the cell's stand-in model
python3 tools/gen_sch.py                      # design.py + sch_layout.py -> root + 4 sheets, project symbols
kicad-cli sch erc --severity-all --exit-code-violations FujiNet-Pocket-Rev0.kicad_sch -o /dev/null
python3 tools/check_pins.py                   # firmware/pocket.h and the link path vs the netlist
python3 tools/bom.py
mkdir -p docs
kicad-cli sch export pdf -o docs/FujiNet-Pocket-Rev0-schematic.pdf FujiNet-Pocket-Rev0.kicad_sch >/dev/null
if [ "${LAYOUT:-0}" = 1 ]; then
    ${PCBNEW_PYTHON:-/usr/bin/python3} tools/gen_pcb.py      # placement.py + design.py -> the placed board, planes, fan-out, shell anchors
    ${PCBNEW_PYTHON:-/usr/bin/python3} tools/set_models.py
    bash tools/route_board.sh
    ${PCBNEW_PYTHON:-/usr/bin/python3} tools/export_fab.py   # gerbers, drill, positions, STEP, renders
fi
rm -f FujiNet-Pocket-Rev0.kicad_prl
echo "build_all: done"
