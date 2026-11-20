#!/usr/bin/env bash
# Regenerate FujiNet Pocket Rev0 (DRAFT): the edge footprint, the schematic (root + 4 sheets, with
# sch_draw's connectivity check, the hierarchy check and netlist parity against design.py), ERC at
# every severity, the firmware pin-map check, the BOM and the schematic PDF.  Needs KiCad 10 and
# Python 3.  tools/harvest_symbols.py refreshes tools/symcache.sexpr from the installed KiCad
# libraries; run it only when design.py takes a new stock symbol.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
python3 tools/make_edge_fp.py >/dev/null      # the Pocket / GB edge footprint
python3 tools/gen_sch.py                      # design.py + sch_layout.py -> root + 4 sheets, project symbols
kicad-cli sch erc --severity-all --exit-code-violations FujiNet-Pocket-Rev0.kicad_sch -o /dev/null
python3 tools/check_pins.py                   # firmware/pocket.h and the link path vs the netlist
python3 tools/bom.py
mkdir -p docs
kicad-cli sch export pdf -o docs/FujiNet-Pocket-Rev0-schematic.pdf FujiNet-Pocket-Rev0.kicad_sch >/dev/null
rm -f FujiNet-Pocket-Rev0.kicad_prl
echo "build_all: done"
