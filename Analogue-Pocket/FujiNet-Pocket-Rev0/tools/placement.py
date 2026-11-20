"""Component placement for gen_pcb.py: design.py key -> (x, y, rot).  KiCad frame, top view of
the component side (F.Cu), y down, rotation CCW; mm.

Board (gen_pcb.py): body x 74.3..125.7 from the top edge Y0 = 68 down to the tab base 141.4; the
49.2 mm tab below with the 32 fingers; insertion edge y = 150.  The Pocket's shell top sits about
SLOT_Y = 119 (31 mm in from the insertion edge, ESTIMATE -- measure a Pocket).  Below that line the
board's flat back lies nearly flush against the Pocket in its cartridge recess, and the component
side (the fingers' side) faces the recess's open side, covered only by the Pocket's lip below about
LIP_Y = 135 (15 mm in, ESTIMATE): there only low parts go.

Fingers (x = 100 + make_edge_fp.pin_x): pin 1 CART_VCC 76.6, pin 5 POCKET_TX 82.75, pin 31
POCKET_RX 121.75, pin 32 GND 123.4.

Regions:
  inside the slot   the RX chain over pin 5 (west), the TX chain over pin 31 (east), the bring-up
                    pads between them, the battery's lead pads, two shell holes
  upper body        the ESP32-S3 top centre, antenna flush with the top edge over its keep-out band
                    (no copper, holes or parts across the whole width there); the reset / boot
                    buttons and the S3's decoupling west of it, the three LEDs down the west edge;
                    the microSD on the east edge (card in from the east); USB-C on the west edge
                    (plug in from the west); under the module, west to east: ESD and CC, the charger
                    and power path, the TPS63001 and its inductor, the CP2102N and auto-program
  the cell          rides on a shelf in the shell over the parts (gen_pcb.CELL), clear of the
                    antenna band and the buttons; its leads come down to J_BAT above the lip
  back (B side)     nothing: it lies against the Pocket
The shell's M2 holes (gen_pcb.HOLES) keep 3 mm rings clear of parts.
"""

SLOT_Y = 119.0
LIP_Y = 135.0


def do_placement(place, fiducials):
    # ---- inside the slot ---------------------------------------------------
    # RX: pin 5 (x 82.75) -> R_RXIN -> RXB_IN (100k down) -> U_RXBUF -> LINK_RX up the west side
    place('R_RXIN', 82.75, 138.0, 90)
    place('R_RXPD', 86.0, 134.0, 90)
    place('U_RXBUF', 90.0, 130.0, 0)
    place('C_RXBUF', 90.0, 125.5, 0)
    # TX: LINK_TX -> (100k down) U_TXBUF on CART_VCC -> R_TXOUT -> pin 31 (x 121.75)
    place('R_TXOUT', 121.75, 138.0, 90)
    place('U_TXBUF', 112.0, 130.0, 0)
    place('R_TXPD', 107.5, 130.0, 90)
    place('C_TXBUF', 112.0, 125.5, 0)
    # bring-up pads: the link, the cart rail, the rails, ground (bench only: inside the slot)
    place('TP_PTX', 86.0, 138.5, 0)
    place('TP_PRX', 117.5, 138.5, 0)
    place('TP_CVCC', 80.0, 122.0, 0)
    place('TP_GNDE', 100.0, 138.5, 0)
    place('TP_VBAT', 96.0, 122.0, 0)
    place('TP_VSYS', 96.5, 106.4, 0)        # by the regulator (VSYS is short)
    place('TP_3V3', 104.0, 122.0, 0)

    # ---- upper body: the module and its west side ----------------------------
    place('U_S3', 100.0, 81.0, 0)            # antenna end at the top edge (courtyard top Y0 + 0.15)
    place('C_S3BULK', 88.9, 77.0, 90)        # by 3V3 (pad 2) and EN (pad 3), below the antenna band
    place('C_S3', 88.9, 80.3, 90)
    place('R_EN', 88.9, 83.4, 90)
    place('C_EN', 88.9, 86.5, 90)
    place('SW_S3EN', 84.5, 82.5, 90)
    place('SW_S3BOOT', 84.5, 91.5, 90)
    # LEDs down the west edge (light pipes in the shell): WiFi, bus, charge
    place('D_LWIFI', 77.3, 84.0, 90)
    place('R_LWIFI', 79.3, 84.0, 90)
    place('D_LBUS', 77.3, 89.0, 90)
    place('R_LBUS', 79.3, 89.0, 90)
    place('D_CHG', 77.3, 94.0, 90)
    place('R_CHGLED', 79.3, 94.0, 90)

    # ---- microSD on the east edge (card in from the east) ----------------------
    place('J_SD', 116.3, 88.5, 90)
    place('RN_SD', 112.0, 100.0, 0)
    place('R_SDCD', 115.6, 100.0, 90)
    place('C_SD', 117.8, 100.0, 90)

    # ---- USB-C on the west edge (plug in from the west), ESD, CC -------------------
    place('J_USB', 77.5, 107.0, 270)
    place('D_ESDV', 85.4, 102.6, 90)
    place('D_ESDP', 85.4, 105.1, 90)
    place('D_ESDM', 85.4, 107.6, 90)
    place('R_CC1', 85.4, 110.6, 90)
    place('R_CC2', 85.4, 113.8, 90)
    place('C_VBUS', 86.6, 98.2, 90)
    place('C_VBUSHF', 84.4, 98.2, 90)

    # ---- charger, power path, enable ----------------------------------------------
    place('U_CHG', 90.4, 99.0, 0)
    place('C_CHGIN', 88.0, 102.6, 0)
    place('C_CHGOUT', 92.8, 102.6, 0)
    place('R_PROG', 90.4, 104.8, 0)
    place('D_VBUS', 90.5, 108.6, 0)
    place('Q_BAT', 89.0, 113.0, 0)
    place('R_VBPD', 92.4, 113.0, 90)
    place('D_EN', 96.0, 113.0, 0)
    place('R_ENPD', 99.4, 113.0, 90)

    # ---- the TPS63001 (datasheet layout: the inductor straight across L1 / L2 on the IC's west
    # side, the input capacitor by VIN, the output capacitors by VOUT, VINA's on the east) ----
    place('U_REG', 101.0, 101.0, 0)
    place('L_REG', 96.7, 101.0, 90)
    place('C_REGIN', 100.6, 104.4, 0)
    place('C_VINA', 105.6, 101.775, 270)   # pad 1 (VSYS) level with VINA (pin 8)
    place('C_REGOUT1', 100.6, 97.6, 0)
    place('C_REGOUT2', 104.6, 97.8, 0)

    # ---- the CP2102N and auto-program -------------------------------------------------
    place('U_UART', 111.0, 108.5, 0)
    place('C_UART', 106.6, 111.8, 90)        # by VDD / VREGIN (pins 6, 7), clear of the USB pins (4, 5) and the north pins
    place('C_UARTBULK', 114.9, 111.0, 90)
    place('R_CPRST', 115.6, 103.8, 90)
    place('R_VBSH', 104.2, 112.6, 90)
    place('R_VBSL', 102.0, 112.6, 90)
    place('U_AUTOPROG', 111.0, 114.6, 0)

    # ---- the cell's leads -------------------------------------------------------------
    # the cell rides on the shell's shelf over the parts (gen_pcb.CELL: x 88..118, y 79..129); its
    # leads come down from its lower end to these pads, above the lip (pad 1 + at x 103, - at x 97)
    place('J_BAT', 100.0, 131.5, 0)

    # ---- the edge -------------------------------------------------------------------
    place('J_EDGE', 100.0, 146.0, 0)        # insertion edge at local y +4.0 -> board y 150

    fiducials += [('FID1', 76.2, 120.0), ('FID2', 123.8, 120.0), ('FID3', 100.0, 128.0)]
