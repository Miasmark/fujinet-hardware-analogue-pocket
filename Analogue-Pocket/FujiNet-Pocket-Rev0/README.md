# FujiNet Pocket Rev0 (draft)

A **FujiNet for the Analogue Pocket's cartridge slot**. On the Pocket the FPGA core is the
cartridge:
- It serves the console's FujiNet mailbox to the running program.
- It sends each request as a FujiBus packet in a SLIP frame at 115,200 baud 8N1, on cartridge
  pin 5, and listens on pin 31.

This board is therefore only the FujiNet half of a FujiNet cartridge: no bus logic, no SRAM, no
console-side microcontroller. It is the same for every Pocket core that speaks this link. The
first is openFPGA-7800 (2.2.7: CONFIG, the network devices and game loading, tested with
fujinet-pc on the link port). An Intellivision core and a 2600 core are scoped to follow.

**Status (2026-11-20): schematic draft only.** It has not been laid out, built or run.

| Check | Result |
|---|---|
| ERC (all severities) | 0 errors, 0 warnings |
| netlist parity (kicad-cli netlist vs `tools/design.py`) | 41 / 41 nets |
| `tools/check_pins.py` (the netlist vs `firmware/pocket.h`, plus the link path) | pass |
| Layout, shell, fit in a Pocket | not started |

`tools/build_all.sh` regenerates everything. It needs KiCad 10 and Python 3.
- The circuit lives in `tools/design.py`.
- The sheet drawings live in `tools/sch_layout.py`.
- The `.kicad_sch` files are output: edit the Python, not them.
- The generator, the drawing toolkit and its checks are FujiNet-7800-Rev0's (`ATARI-7800/`).

## Block diagram

```
Pocket slot ──pin 5──100R──[LVC1G34 on +3V3]──────── UART1 RX (IO17) ┐
            ──pin 31─100R──[LVC1G34 on CART_VCC]──── UART1 TX (IO18) ├ ESP32-S3-WROOM-1-N16R8 ── microSD
            ──pin 1 (CART_VCC) ─┐                                    │   UART0 ── CP2102N ── USB-C
                                └─ BAT54C ─ PWR_EN ─ TPS63001 (3.3 V)┘                         │
                                     VBUS ─┘           ▲ VSYS                                  │
                         LiPo ── AO3401A ──────────────┤                                       │
                          ▲                 SS34 ──────┘◄────────────── VBUS ◄────────────────┘
                          └── MCP73831 (4.20 V, 213 mA) ◄── VBUS
```

## The slot side (sheet 2)

The Pocket's slot is a GB / GBA edge: 32 fingers at 1.5 mm on one face.

| Pin | GBA / GB name | Net | Use |
|---|---|---|---|
| 1 | VCC | CART_VCC | The cart rail: 3.3 V while the Pocket runs with cart power on. The core asks for it (`core.json` `cartridge_adapter` 0). |
| 5 | /CS | POCKET_TX | The core's TX, idle high. |
| 31 | /REQ (GB: VIN) | POCKET_RX | The core's RX. |
| 32 | GND | GND | |
| others | | open | Analogue's template leaves them as they are: bank 0 an output held high, the rest inputs. |

- **Two SN74LVC1G34 buffers, both with Ioff** (partial power-down), so neither side ever feeds the
  other when it is off:
  - **RX buffer:** runs on the device's +3V3.
  - **TX buffer:** runs on the Pocket's own rail (pin 1).
  - The Pocket can be on with the device's cell flat, and the device can be on (charging, flashing)
  with the Pocket off.
- **100R in series at each finger.**
- **100k pull-downs** hold an unpowered side's line low:
  - The core counts a line only once it has idled high for 1 ms, so a low pin 31 is never heard.
  - The S3 sees a break, not noise.
- **Pin 1 also feeds the enable diode:** about 30 uA.

**Edge geometry** (`tools/make_edge_fp.py`) is re-drawn from Gekkio's GB-CART32K-A (gb-hardware,
CC-BY-4.0):
- pins 2-31 are 1.0 x 5.5 mm;
- pins 1 and 32 are 1.3 x 6.0 mm, so the rail and ground make contact first;
- the tab is 49.2 x 8.6 mm;
- the board is 1.0 mm thick.

**To verify on a Pocket before ordering boards:** which face the fingers are on, and pin 1.

## The FujiNet half (sheets 3 and 4)

FujiNet-7800-Rev0's circuits, unchanged except as noted:
- **ESP32-S3-WROOM-1-N16R8:** with its EN RC, S3_RST and S3_BOOT buttons, and 22 uF bulk.
- **microSD:** TF-015, SPI, with pull-ups.
- **USB-C:** HRO TYPE-C-31-M-12, 5.1k Rd, ESD.
- **CP2102N:** on UART0, with the UMH3N esptool auto-program pair.

Changed:
- **The link:** UART1 on IO17 (RX) and IO18 (TX) replaces the RP2354B's native USB and its
  RUN / BOOTSEL lines.
- **Status LEDs:** two plain LEDs, active low from +3V3, replace the WS2812C, which needs 3.7 V
  or more; this board has no 5 V rail.
  - WiFi: green, IO14.
  - Bus: red, IO16.

## Power (sheet 5)

The device powers itself. The Pocket's cart rail has only been seen to supply about 0.2 W. An
ESP32-S3 on WiFi averages more than that and peaks several times higher (openFPGA-7800
`docs/FUJINET_POCKET_DEVICE.md`, section 5).

- **Cell:** a protected 1S LiPo pouch, for example a 303450 or 403450 (400-600 mAh), on a JST-PH.
  - The board has no protection circuit of its own: the cell's is relied on.
  - **Check the cell's polarity: JST-PH cells come wired both ways.**
- **Charger:** MCP73831-2 (4.20 V), 213 mA (R_PROG 4.7k, about 0.5 C for 400 mAh), from USB
  only, with a charge LED.
- **Power path** (Microchip AN1149, as the 7800 board's 5 V OR):
  - USB VBUS goes through an SS34 onto VSYS.
  - The cell goes through an AO3401A, gate on VBUS: on without USB, off with it, so USB runs the
    board while the cell charges.
  - 4.7k holds the gate down against the SS34's leakage.
- **3.3 V:** a TPS63001 buck-boost, 1.8-5.5 V in. It holds 3.3 V over the cell's whole 3.0-4.2 V
  and through WiFi bursts.
  - PS/SYNC is tied low: power-save mode at light load.
- **Enable:** `PWR_EN = CART_VCC or VBUS` (BAT54C, 100k down).
  - The board runs while the Pocket is on, or while USB is in (charging, flashing).
  - Otherwise the regulator is shut down: no power switch is needed.

## Firmware

`firmware/pocket.h` and `firmware/platformio-fujinet-pocket.ini` are proposed for fujinet-firmware
as `include/pinmap/pocket.h` and `build-platforms/platformio-fujinet-pocket.ini`:
- **The build:** the generic RS232 build (`BUILD_RS232`) on a wired UART, as `rs232_s3.h`.
- **Pin assignments:**
  - **UART1:** the link, on 17 and 18. Defining `PIN_UART1_RX` is what selects the wired UART in
    `lib/bus/rs232/rs232.h`.
  - **SD and UART0:** as `fujiversal-rs232.h`.
  - **LEDs:** on 14 and 16.
  - **Not used:** the modem control lines and keys.cpp's buttons are `GPIO_NUM_NC`.
    `common.h` would otherwise put button C on GPIO14, this board's WiFi LED.

`pinmap.h` also needs its `#include "pinmap/pocket.h"`. Neither file has been compiled yet.

## Before layout

1. **Edge:** check the finger face, pin 1 and the board thickness (1.0 mm, as Gekkio's GB
   boards) against a GB cartridge in a Pocket.
2. **Shell and outline:** the board is a GB-cart-sized body with a GBA-shaped lower corner, so the
   Pocket's voltage switch stays unpressed and the slot stays at 3.3 V. A GB/GBC-shaped corner
   puts the slot at 5 V. The device notes in openFPGA-7800 say to cut it 0.5-1 mm deeper and wider
   than a GBA cart's.
   - **Inside the slot:** the edge, the buffers and the enable.
   - **Above the Pocket:** the module with its antenna at the top edge, clear of the Pocket's
     back; also the cell, USB-C, microSD and the LEDs.
   - Print a blank first.
3. **Sourcing:** no LCSC code chosen yet for SN74LVC1G34DBVR, MCP73831T-2ACI/OT, TPS63001DRCR,
   SWPA4030S1R5NT, S2B-PH-SM4-TB and the green LED (`FujiNet-Pocket-Rev0-BOM.csv`).
4. **The inductor's saturation current** against the TPS63001's switch current limit (datasheet).
5. **The microSD card-detect polarity:** it is wired to IO42 and set NC in `pocket.h` until known.
6. **Compile `pocket.h`** in fujinet-firmware; offer the pin map upstream once a board has run.
7. **Silkscreen:** the link to github.com/FujiNetWIFI that this repository's notice requires on
   any product made from these designs.

## Files

| Path | What |
|---|---|
| `tools/design.py` | The circuit: every part, value, footprint, MPN, LCSC code and net. |
| `tools/sch_layout.py` | How each sheet is drawn. |
| `tools/gen_sch.py`, `sch_draw.py`, `sexpr.py` | The generator and its checks (FujiNet-7800-Rev0's). |
| `tools/harvest_symbols.py`, `symcache.sexpr` | The stock symbols embedded in the sheets. |
| `tools/make_edge_fp.py` | The slot edge footprint. |
| `tools/check_pins.py` | The netlist against `firmware/pocket.h` and the link path. |
| `tools/bom.py` | `FujiNet-Pocket-Rev0-BOM.csv`. |
| `firmware/` | The proposed fujinet-firmware pin map and build env. |
| `docs/FujiNet-Pocket-Rev0-schematic.pdf` | The schematic. |

## Provenance and license

**CERN-OHL-W-2.0**, as FujiNet-7800-Rev0.
- **The FujiNet half, the generators and the drawing toolkit:** `ATARI-7800/FujiNet-7800-Rev0` in
  this repository, and through it SMS / NES Rev0.
- **The slot side, the LEDs and the power sheet:** new.
- **Edge geometry:** Gekkio, gb-hardware GB-CART32K-A, CC-BY-4.0 (measurements re-drawn).
- **The link protocol and pins:** openFPGA-7800 (MIT), `docs/FUJINET_POCKET_DEVICE.md`,
  `src/fpga/core/fujinet_mailbox.sv`.
- **Symbols and footprints:** official KiCad libraries (CC-BY-SA 4.0 with exception), except the
  project's own (the Pocket edge; the TF-015 microSD from FujiNet-7800-Rev0).
