"""How each sheet is drawn: placement and wiring, one function per sheet, and the root's block
diagram.

design.py owns the circuit; these functions only say where each part sits and how its pins are
joined (sch_draw.Sheet), left to right in signal-flow order starting at the cartridge slot.  Parts
are addressed by their design.py key, never by reference.  sch_draw.Sheet.check(),
gen_sch.check_hierarchy() and gen_sch.netlist_parity() prove the drawing is exactly design.py's
netlist, so a wiring slip here fails the build.

esp32s3_sd() and usb_uart() are FujiNet-7800-Rev0's drawings (fujinet-hardware, CERN-OHL-W-2.0),
the first with the RP2354B's lines and the WS2812 replaced by the link UART and two LEDs; edge(),
power() and the root are this board's.
"""
import design as D
from sch_draw import Sheet, Pt, snap

DRAW = {}


class KSheet(Sheet):
    """A Sheet whose parts are addressed by design.py key (references also work)."""
    def place(self, ref, *a, **k):
        return Sheet.place(self, D.KEY.get(ref, ref), *a, **k)

    def N(self, ref, net):
        return Sheet.N(self, D.KEY.get(ref, ref), net)

    def P(self, ref, num, unit=None):
        return Sheet.P(self, D.KEY.get(ref, ref), num, unit)


def sheet(stem, paper='A3'):
    def deco(f):
        DRAW[stem] = (f, paper)
        return f
    return deco


def draw(stem, syms, parts):
    f, paper = DRAW[stem]
    sh = KSheet(stem, syms, parts, paper)
    f(sh)
    return sh


def ncs(sh, key, unit=1):
    """No-connect flags on every unused pin of a placed unit."""
    ref = D.KEY[key]
    for num, pt in sh.placed[(ref, unit)]['pins'].items():
        if sh.parts[ref].pins[num] is None:
            sh.nc(pt)


def tap_tp(sh, key, pt, up=True, fields='right'):
    """A test pad on a T off the wire through pt (pad body above / below the line)."""
    x, y = pt
    ty = y - 5.08 if up else y + 5.08
    sh.place(key, x, ty, rot=0 if up else 180, fields=fields)
    sh.wire(sh.P(key, 1), (x, y))


# =========================================================================
@sheet('edge', 'A4')
def edge(sh):
    """The Pocket's slot on the left, everything but its rail, ground and two link pins left open.
    Pin 5 (the core's TX) comes in through 100R into the RX buffer on the device's +3V3 and leaves
    as LINK_RX; LINK_TX from the S3 goes out through the TX buffer, powered from the slot's own
    rail, and 100R to pin 31 (the core's RX).  The rail (pin 1) leaves as CART_VCC for the power
    sheet's enable."""
    J = 'J_EDGE'
    X, Y = 60.96, 104.14
    sh.place(J, X, Y, fields='abovebelow', ref_at=(X + 3.81, Y - 36.83, 'left'), val_at=(X + 3.81, Y + 36.83, 'left'))
    ncs(sh, J)
    col = 160.02
    sh.gnd(sh.P(J, 32))
    # CART_VCC: pin 1 up and out along the top, a bring-up pad and the PWR_FLAG on it
    v = sh.P(J, 1)
    ty = 50.8
    sh.wire(v, (v[0], ty), (91.44, ty), (col, ty))
    sh.hlabel(Pt(col, ty), 'CART_VCC', 'R', 'output')
    tap_tp(sh, 'TP_CVCC', (76.2, ty))
    sh.flag((91.44, ty), 'CART_VCC')
    sh.place('TP_GNDE', 76.2, 134.62, fields='right')
    sh.gnd(sh.P('TP_GNDE', 1))
    # RX: pin 5 -> 100R -> (100k down) -> buffer on +3V3 -> LINK_RX
    p = sh.P(J, 5)
    ry = p[1]
    tap_tp(sh, 'TP_PTX', (76.2, ry))
    sh.place('R_RXIN', 91.44, ry, rot=90, fields='above')
    sh.wire(p, sh.N('R_RXIN', 'POCKET_TX'))
    sh.label((p[0] + 1.27, ry), 'POCKET_TX')
    sh.place('R_RXPD', 99.06, ry + 3.81, fields='right')
    sh.gnd(sh.P('R_RXPD', 2))
    B = 'U_RXBUF'
    sh.place(B, 119.38, ry, fields='abovebelow', ref_at=(124.46, ry - 8.89, 'left'), val_at=(124.46, ry + 8.89, 'left'))
    sh.wire(sh.N('R_RXIN', 'RXB_IN'), sh.P('R_RXPD', 1), sh.P(B, 2))
    sh.label((100.33, ry), 'RXB_IN')
    sh.sup(sh.P(B, 5), '+3V3')
    sh.gnd(sh.P(B, 3))
    sh.nc(sh.P(B, 1))
    sh.wire(sh.P(B, 4), (col, ry))
    sh.hlabel(Pt(col, ry), 'LINK_RX', 'R', 'output')
    sh.place('C_RXBUF', 99.06, ry - 11.43)
    sh.sup(sh.P('C_RXBUF', 1), '+3V3')
    sh.gnd(sh.P('C_RXBUF', 2))
    # TX: LINK_TX (100k down) -> buffer on CART_VCC -> 100R -> pin 31
    q = sh.P(J, 31)
    ty2 = Y
    sh.wire(q, (78.74, q[1]), (78.74, ty2), (82.55, ty2))
    tap_tp(sh, 'TP_PRX', (81.28, ty2), up=False)
    sh.label((q[0] + 1.27, q[1]), 'POCKET_RX')
    sh.place('R_TXOUT', 86.36, ty2, rot=90, fields='above')
    T = 'U_TXBUF'
    sh.place(T, 114.3, ty2, mirror='y', fields='abovebelow', ref_at=(104.14, ty2 - 8.89, 'right'),
             val_at=(104.14, ty2 + 8.89, 'right'))
    sh.wire(sh.N('R_TXOUT', 'TXB_OUT'), sh.P(T, 4))
    sh.label((93.98, ty2), 'TXB_OUT')
    sh.gnd(sh.P(T, 3))
    sh.nc(sh.P(T, 1))
    vc = sh.P(T, 5)
    cy = vc[1] - 5.08
    sh.place('C_TXBUF', 127.0, cy + 3.81)
    sh.wire(vc, (vc[0], cy), sh.P('C_TXBUF', 1))
    sh.gnd(sh.P('C_TXBUF', 2))
    sh.name((vc[0], cy), 'CART_VCC', 'U', 'R')
    sh.place('R_TXPD', 139.7, ty2 + 3.81, fields='right')
    sh.gnd(sh.P('R_TXPD', 2))
    sh.wire((col, ty2), sh.P('R_TXPD', 1), sh.P(T, 2))
    sh.hlabel(Pt(col, ty2), 'LINK_TX', 'R', 'input')
    sh.text((30.48, 160.02),
            'The Pocket\'s slot: pin 1 the cart rail (3.3 V with the Pocket on), 5 the core\'s TX (GBA /CS), 31 its RX\n'
            '(GBA /REQ), 32 ground; the rest left open, as Analogue\'s template leaves them.  Both buffers are LVC with\n'
            'Ioff: the RX one on the device\'s +3V3, the TX one on the Pocket\'s own rail, so neither side back-feeds the\n'
            'other when it is off.  The 100k pull-downs hold an unpowered side low: the core hears a line only once it\n'
            'has idled high for 1 ms.')


# =========================================================================
@sheet('esp32s3-sd', 'A4')
def esp32s3_sd(sh):
    """The ESP32-S3: reset / boot on the left, the WiFi LED below them; the UART to the USB bridge
    and the link UART to the slot on the right, the bus LED, then the microSD socket (SPI fanned out
    to the socket's pin order)."""
    U = 'U_S3'
    X, Y = 190.5, 149.86
    sh.place(U, X, Y, fields='abovebelow', ref_at=(X - 12.7, Y - 29.21, 'left'), val_at=(X - 22.86, Y + 33.02, 'right'))
    lcol, rcol = 124.46, 297.18
    # supply + decoupling above
    v = sh.P(U, 2)
    node = (v[0], Y - 38.1)
    sh.wire(v, node, (X + 10.16, node[1]), (X + 22.86, node[1]))
    sh.sup(node, '+3V3')
    for c, x in (('C_S3', X + 10.16), ('C_S3BULK', X + 22.86)):
        sh.place(c, x, node[1] + 3.81)
        sh.gnd(sh.P(c, 2))
    sh.gnd(sh.P(U, 1))
    # EN: pull-up, power-on delay, button; S3_EN also from the auto-program pair
    en = sh.P(U, 3)
    ey = en[1] - 17.78
    sh.wire(en, (X - 20.32, en[1]), (X - 20.32, ey), (X - 27.94, ey), (X - 38.1, ey), (X - 48.26, ey), (lcol, ey))
    sh.hlabel(Pt(lcol, ey), 'S3_EN', 'L', 'bidirectional')
    sh.place('R_EN', X - 27.94, ey - 3.81, fields='right')
    sh.sup(sh.P('R_EN', 1), '+3V3')
    sh.place('C_EN', X - 38.1, ey + 3.81, fields='right')
    sh.gnd(sh.P('C_EN', 2))
    sh.place('SW_S3EN', X - 48.26, ey + 5.08, rot=270, fields='left')
    sh.gnd(sh.P('SW_S3EN', 2))
    # IO0 (BOOT): button + the auto-program transistor
    io0 = sh.P(U, 27)
    sh.wire(io0, (X - 43.18, io0[1]), (lcol, io0[1]))
    sh.hlabel(Pt(lcol, io0[1]), 'S3_IO0', 'L', 'bidirectional')
    sh.place('SW_S3BOOT', X - 43.18, io0[1] + 5.08, rot=270, fields='left')
    sh.gnd(sh.P('SW_S3BOOT', 2))
    # WiFi (IO14, jogged up to its own row) and bus (IO16) LEDs, active low: +3V3 -> 1k -> LED -> GPIO
    for pad, net, d, r, row in ((22, 'LED_WIFI', 'D_LWIFI', 'R_LWIFI', Y + 7.62),
                                (9, 'LED_BUS', 'D_LBUS', 'R_LBUS', Y + 22.86)):
        w = sh.P(U, pad)
        sh.place(d, X - 40.64, row, rot=180, fields='below')
        sh.place(r, X - 55.88, row, rot=90, fields='below')
        if row != w[1]:
            sh.wire(w, (X - 20.32, w[1]), (X - 20.32, row), sh.N(d, net))
        else:
            sh.wire(w, sh.N(d, net))
        sh.label((X - 33.02, row), net)
        sh.wire(sh.N(r, net + '_A'), sh.N(d, net + '_A'))
        sh.sup(sh.N(r, '+3V3'), '+3V3', rot=90)
        sh.name((X - 48.26, row), net + '_A', 'U', 'L')
    # UART0 to the CP2102N, UART1 to the slot
    for pad, n, shape in ((37, 'S3_TXD', 'output'), (36, 'S3_RXD', 'input'), (10, 'LINK_RX', 'input'),
                          (11, 'LINK_TX', 'output')):
        p = sh.P(U, pad)
        sh.wire(p, (rcol, p[1]))
        sh.hlabel(Pt(rcol, p[1]), n, 'R', shape)
    ncs(sh, U)
    # microSD: SPI fans out from 2.54 to the socket's 5.08 and is named there
    J = 'J_SD'
    sh.place(J, X + 76.2, Y + 20.32, fields='abovebelow', ref_at=(X + 88.9, Y + 46.99, 'left'),
             val_at=(X + 88.9, Y + 49.53, 'left'))
    for k, n in enumerate(('SD_MOSI', 'SD_SCK', 'SD_MISO', 'SD_CS', 'SD_CD')):
        a, b2 = sh.N(U, n), sh.N(J, n)
        x = X + 22.86 + (4 - k) * 2.54
        sh.wire(a, (x, a[1]), (x, b2[1]), b2)
        sh.label((X + 38.1, b2[1]), n)
    # pull-ups: DAT1 / DAT2 wired to the pack (DAT2 steps down to its pin), CS / MISO by label
    R = 'RN_SD'
    sh.place(R, X + 43.18, sh.N(J, 'SD_DAT1')[1], rot=90, mirror='x', fields='above')
    sh.wire(sh.N(R, 'SD_DAT1'), sh.N(J, 'SD_DAT1'))
    p, q = sh.N(R, 'SD_DAT2'), sh.N(J, 'SD_DAT2')
    sh.wire(p, (X + 50.8, p[1]), (X + 50.8, q[1]), q)
    sh.label((X + 53.34, sh.N(J, 'SD_DAT1')[1]), 'SD_DAT1')
    sh.label((X + 53.34, q[1]), 'SD_DAT2')
    for n in ('SD_CS', 'SD_MISO'):
        e = sh.stub(sh.N(R, n), 2.54)
        sh.label(e, n, 'R')
    g = [sh.P(R, n) for n in (5, 6, 7, 8)]
    ys = sorted(p[1] for p in g)
    gx = g[0][0] - 2.54
    for p in g:
        sh.wire(p, (gx, p[1]))
    sh.wire(*[(gx, y) for y in ys])
    sh.sup((gx, ys[0]), '+3V3')
    sh.place('R_SDCD', X + 104.14, Y + 38.1, fields='right')
    sh.sup(sh.P('R_SDCD', 1), '+3V3')
    e = sh.stub(sh.P('R_SDCD', 2))
    sh.label(e, 'SD_CD', 'D')
    sh.sup(sh.N(J, '+3V3'), '+3V3', n=2.54, rot=90)
    sh.gnd(sh.P(J, 6), n=2.54, rot=270)
    shp = [sh.P(J, n) for n in (10, 11, 12, 13)]
    sh.wire(*shp)
    sh.wire(shp[0], (shp[0][0], shp[0][1] + 2.54))
    sh.gnd((shp[0][0], shp[0][1] + 2.54))
    sh.place('C_SD', X + 93.98, Y + 38.1)
    sh.sup(sh.P('C_SD', 1), '+3V3')
    sh.gnd(sh.P('C_SD', 2))


# =========================================================================
@sheet('usb-uart', 'A4')
def usb_uart(sh):
    """USB-C on the left; VBUS up onto its rail (ESD, decoupling, the bridge's VBUS sense), CC
    pull-downs, the data pair through its ESD diodes into the CP2102N; the bridge's UART and the
    esptool auto-program pair on the right."""
    J, U = 'J_USB', 'U_UART'
    rcol = 284.48
    sh.place(J, 50.8, 149.86, fields='abovebelow', val_at=(39.37, 172.72, 'right'))
    vb = sh.P(J, 'A4')
    ry = 116.84
    xs = [96.52, 109.22, 121.92]
    sh.wire(vb, (71.12, vb[1]), (71.12, ry), *[(x, ry) for x in xs], (134.62, ry))
    sh.sup((71.12, ry), 'VBUS')
    for key, x in zip(('D_ESDV', 'C_VBUS', 'C_VBUSHF'), xs):
        sh.place(key, x, ry + 3.81, rot=270 if key == 'D_ESDV' else 0, fields='left' if key == 'D_ESDV' else 'right')
        sh.gnd(sh.P(key, 2))
    for pin, key, x, f in (('A5', 'R_CC1', 83.82, 'above'), ('B5', 'R_CC2', 96.52, 'below')):
        p = sh.P(J, pin)
        sh.place(key, x, p[1], rot=90, fields=f)
        sh.wire(p, sh.P(key, 1))
        sh.gnd(sh.P(key, 2), 2.54, rot=90)
        sh.label((p[0] + 2.54, p[1]), pin.replace('A5', 'CC1').replace('B5', 'CC2'))
    dm = [sh.P(J, 'A7'), sh.P(J, 'B7')]
    dp = [sh.P(J, 'A6'), sh.P(J, 'B6')]
    for a, b in (dm, dp):
        sh.wire(a, (68.58, a[1]), (68.58, b[1]), b)
    sh.place(U, 190.5, 160.02, fields='abovebelow', val_at=(204.47, 196.85, 'left'))
    cdm, cdp = sh.P(U, 5), sh.P(U, 4)
    sh.wire((68.58, dm[0][1]), (114.3, dm[0][1]), cdm)
    sh.wire((68.58, dp[0][1]), (99.06, dp[0][1]), (167.64, dp[0][1]), (167.64, cdp[1]), cdp)
    sh.place('D_ESDM', 114.3, dm[0][1] - 3.81, rot=90, fields='right')
    sh.gnd(sh.P('D_ESDM', 2), rot=180)
    sh.place('D_ESDP', 99.06, dp[0][1] + 3.81, rot=270, fields='right')
    sh.gnd(sh.P('D_ESDP', 2))
    sh.label((139.7, dm[0][1]), 'UBRG_DM')
    sh.label((139.7, dp[0][1]), 'UBRG_DP')
    for p in (sh.P(J, 'A8'), sh.P(J, 'B8')):
        sh.nc(p)
    g1, g2 = sh.P(J, 'A1'), sh.P(J, 'SH')
    sh.wire(g2, (g2[0], g2[1] + 2.54), (g1[0], g1[1] + 2.54), g1)
    sh.gnd((g1[0], g1[1] + 2.54))
    sns = sh.P(U, 8)
    sh.place('R_VBSH', 134.62, ry + 3.81, fields='right')
    sh.place('R_VBSL', 144.78, sns[1] - 3.81, rot=180, fields='right')
    sh.wire(sh.P('R_VBSH', 2), (134.62, sns[1]), sh.P('R_VBSL', 1), sns)
    sh.gnd(sh.P('R_VBSL', 2), rot=180)
    sh.label((149.86, sns[1]), 'VBUS_SNS')
    vd, vr = sh.P(U, 6), sh.P(U, 7)
    top = 116.84
    sh.wire(vr, (vr[0], top))
    sh.wire(vd, (vd[0], top), (198.12, top), (210.82, top))
    sh.wire((vr[0], top), (vd[0], top))
    sh.sup((vr[0], top), '+3V3')
    for c, x in (('C_UART', 198.12), ('C_UARTBULK', 210.82)):
        sh.place(c, x, top + 3.81)
        sh.gnd(sh.P(c, 2))
    rst = sh.P(U, 9)
    sh.place('R_CPRST', 165.1, rst[1] - 3.81, fields='left')
    sh.wire(rst, (165.1, rst[1]))
    sh.sup(sh.P('R_CPRST', 1), '+3V3')
    sh.label((166.37, rst[1]), 'CP_RST')
    sh.gnd(sh.P(U, 3))
    sh.gnd(sh.P(U, 23), 2.54, rot=90)                      # /CTS tied low
    ncs(sh, U)
    for pad, n, shape in ((26, 'S3_RXD', 'output'), (25, 'S3_TXD', 'input')):
        p = sh.P(U, pad)
        sh.wire(p, (rcol, p[1]))
        sh.hlabel(Pt(rcol, p[1]), n, 'R', shape)
    rts, dtr = sh.P(U, 24), sh.P(U, 28)
    Q = 'U_AUTOPROG'
    sh.place(Q, 248.92, 149.86, unit=1, fields='right')
    sh.place(Q, 248.92, 172.72, unit=2, fields='right')
    b1, e1, c1 = sh.P(Q, 2), sh.P(Q, 1), sh.P(Q, 6)
    b2, e2, c2 = sh.P(Q, 5), sh.P(Q, 4), sh.P(Q, 3)
    sh.wire(rts, (231.14, rts[1]), (231.14, e1[1] + 5.08), (231.14, b2[1]), b2)
    sh.wire((231.14, e1[1] + 5.08), (e1[0], e1[1] + 5.08), e1)
    sh.wire(dtr, (226.06, dtr[1]), (226.06, b1[1]), b1)
    sh.wire((226.06, b1[1]), (226.06, e2[1] + 5.08), (e2[0], e2[1] + 5.08), e2)
    sh.label((215.9, rts[1]), 'UART_RTS')
    sh.label((215.9, dtr[1]), 'UART_DTR')
    for c, n in ((c1, 'S3_EN'), (c2, 'S3_IO0')):
        sh.wire(c, (c[0], c[1] - 2.54), (rcol, c[1] - 2.54))
        sh.hlabel(Pt(rcol, c[1] - 2.54), n, 'R', 'output')


# =========================================================================
@sheet('power', 'A4')
def power(sh):
    """Top: the charger, USB VBUS into the cell (VBAT), its charge LED.  Below, left to right: the
    power path (VBUS through the SS34, the cell through the P-FET) onto VSYS, the TPS63001 that
    makes +3V3 from it, and its enable: the Pocket's rail or USB, through the BAT54C."""
    # -- charger
    U = 'U_CHG'
    X, Y = 60.96, 76.2
    sh.place(U, X, Y, fields='abovebelow', ref_at=(X + 2.54, Y - 8.89, 'left'), val_at=(X + 2.54, Y + 8.89, 'left'))
    sh.sup(sh.P(U, 4), 'VBUS')
    sh.gnd(sh.P(U, 2))
    sh.place('C_CHGIN', 33.02, 72.39, fields='right')
    sh.sup(sh.P('C_CHGIN', 1), 'VBUS')
    sh.gnd(sh.P('C_CHGIN', 2))
    pr = sh.P(U, 5)
    sh.place('R_PROG', 45.72, pr[1] + 3.81, fields='left')
    sh.wire(pr, sh.P('R_PROG', 1))
    sh.gnd(sh.P('R_PROG', 2))
    sh.name((49.53, pr[1]), 'CHG_PROG', 'D', 'D')
    vb = sh.P(U, 3)
    by = vb[1]
    sh.place('C_CHGOUT', 78.74, by - 3.81, rot=180, fields='right')
    sh.gnd(sh.P('C_CHGOUT', 2), rot=180)
    sh.place('J_BAT', 124.46, by, fields='right')
    sh.wire(vb, sh.P('C_CHGOUT', 1), (88.9, by), (96.52, by), sh.P('J_BAT', 1))
    sh.gnd(sh.P('J_BAT', 2))
    tap_tp(sh, 'TP_VBAT', (88.9, by))
    sh.sup((96.52, by), 'VBAT')
    st = sh.P(U, 1)
    sh.place('D_CHG', 91.44, st[1], fields='below')
    sh.wire(st, sh.N('D_CHG', 'CHG_STAT'))
    sh.label((73.66, st[1]), 'CHG_STAT')
    sh.place('R_CHGLED', 104.14, st[1], rot=270, fields='below')
    sh.wire(sh.N('D_CHG', 'CHG_LED_A'), sh.N('R_CHGLED', 'CHG_LED_A'))
    sh.name((97.79, st[1]), 'CHG_LED_A', 'U', 'L')
    sh.sup(sh.N('R_CHGLED', 'VBUS'), 'VBUS', rot=270)
    # -- power path onto VSYS
    vy = 114.3
    sh.place('D_VBUS', 60.96, vy, rot=180, fields='above')
    sh.sup(sh.P('D_VBUS', 2), 'VBUS', rot=90)
    Q = 'Q_BAT'
    sh.place(Q, 73.66, 129.54, mirror='x', fields='right')
    s_, d_, g_ = sh.P(Q, 2), sh.P(Q, 3), sh.P(Q, 1)
    sh.wire(sh.P('D_VBUS', 1), (s_[0], vy))
    sh.wire(s_, (s_[0], vy))
    sh.sup(sh.stub(d_, 5.08), 'VBAT', rot=180)
    sh.place('R_VBPD', 63.5, g_[1] + 3.81, fields='left')
    sh.wire(g_, sh.P('R_VBPD', 1), (58.42, g_[1]))
    sh.sup((58.42, g_[1]), 'VBUS', rot=90)
    sh.gnd(sh.P('R_VBPD', 2))
    # VSYS: bulk, the regulator's VIN / VINA
    R = 'U_REG'
    RX, RY = 134.62, 124.46
    sh.place(R, RX, RY, fields='abovebelow', ref_at=(RX - 5.08, RY - 15.24, 'left'), val_at=(RX + 5.08, RY + 19.05, 'left'))
    caps = [('C_REGIN', 86.36), ('C_VINA', 96.52)]
    vin = sh.P(R, 5)
    sh.wire((s_[0], vy), (s_[0] + 5.08, vy), *[(x, vy) for _, x in caps], (101.6, vy), (109.22, vy), (121.92, vy), vin)
    sh.sup((s_[0] + 5.08, vy), 'VSYS')
    sh.flag((101.6, vy), 'VSYS')
    for c, x in caps:
        sh.place(c, x, vy + 3.81)
        sh.gnd(sh.P(c, 2))
    tap_tp(sh, 'TP_VSYS', (109.22, vy))
    va = sh.P(R, 8)
    sh.wire(va, (121.92, va[1]), (121.92, vy))
    # PS/SYNC low: power-save mode
    ps = sh.P(R, 7)
    sh.wire(ps, (114.3, ps[1]), (114.3, 137.16))
    sh.gnd((114.3, 137.16))
    # the inductor between L1 and L2, beside the regulator
    l1, l2 = sh.P(R, 4), sh.P(R, 2)
    sh.place('L_REG', 119.38, (l1[1] + l2[1]) / 2, fields='left')
    sh.wire(l1, (119.38, l1[1]), sh.P('L_REG', 1))
    sh.wire(l2, (119.38, l2[1]), sh.P('L_REG', 2))
    sh.name((121.92, l1[1]), 'REG_L1', 'D', 'D')
    sh.name((121.92, l2[1]), 'REG_L2', 'D', 'D')
    sh.wire(sh.P(R, 9), sh.P(R, 3))
    sh.gnd(sh.P(R, 3))
    # +3V3 out, FB to VOUT
    vo, fb = sh.P(R, 1), sh.P(R, 10)
    outs = [('C_REGOUT1', 154.94), ('C_REGOUT2', 165.1)]
    sh.wire(vo, (147.32, vo[1]), *[(x, vo[1]) for _, x in outs], (172.72, vo[1]), (180.34, vo[1]))
    sh.wire(fb, (147.32, fb[1]), (147.32, vo[1]))
    sh.sup((180.34, vo[1]), '+3V3')
    for c, x in outs:
        sh.place(c, x, vo[1] + 3.81)
        sh.gnd(sh.P(c, 2))
    tap_tp(sh, 'TP_3V3', (172.72, vo[1]))
    # enable: CART_VCC or VBUS through the BAT54C, 100k down
    E = 'D_EN'
    sh.place(E, 111.76, 152.4, mirror='x', fields='below')
    k = sh.P(E, 3)
    en = sh.P(R, 6)
    sh.wire(k, (k[0], en[1]), en)
    sh.place('R_ENPD', 104.14, 128.27, fields='right')
    sh.wire((k[0], 124.46), (104.14, 124.46), sh.P('R_ENPD', 1))
    sh.gnd(sh.P('R_ENPD', 2))
    sh.name((k[0], 142.24), 'PWR_EN', 'L', 'L')
    sh.sup(sh.P(E, 2), 'VBUS', rot=270)
    a1 = sh.P(E, 1)
    sh.wire(a1, (33.02, a1[1]))
    sh.hlabel(Pt(33.02, a1[1]), 'CART_VCC', 'L', 'input')
    # PWR_FLAGs: GND and VBUS reach the board only through connector (passive) pins
    sh.wire((25.4, 134.62), (35.56, 134.62))
    sh.gnd((25.4, 134.62))
    sh.flag((35.56, 134.62), 'GND')
    sh.wire((25.4, 124.46), (35.56, 124.46))
    sh.sup((25.4, 124.46), 'VBUS')
    sh.flag((35.56, 124.46), 'VBUS')
    sh.text((30.48, 167.64),
            'USB VBUS charges the cell (MCP73831-2, 4.20 V, 213 mA) and, through the SS34, runs the board; without USB\n'
            'the AO3401A (gate = VBUS) puts the cell on VSYS.  The TPS63001 makes 3.3 V over the cell\'s whole range.\n'
            'It runs while the Pocket\'s cart rail (CART_VCC) or USB is up: the board sleeps with the Pocket.')


# =========================================================================
def draw_root(syms):
    """The block diagram: the slot on the left, the ESP32-S3 it talks to, the USB bridge on the
    right; power below, its enable from the slot's rail."""
    sh = KSheet('root', syms, [], 'A3')
    i, o, b = 'input', 'output', 'bidirectional'
    Y0 = 45.72
    ep = sh.block('edge', 30.48, Y0, 33.02, 20.32, right=[('LINK_RX', o), ('LINK_TX', i), None, ('CART_VCC', o)])
    es = sh.block('esp32s3-sd', 124.46, Y0, 50.8, 20.32,
                  left=[('LINK_RX', i), ('LINK_TX', o)],
                  right=[('S3_EN', b), ('S3_TXD', o), ('S3_RXD', i), ('S3_IO0', b)])
    us = sh.block('usb-uart', 220.98, Y0, 45.72, 20.32,
                  left=[('S3_EN', o), ('S3_TXD', i), ('S3_RXD', o), ('S3_IO0', o)])
    pw = sh.block('power', 124.46, 96.52, 50.8, 20.32, left=[('CART_VCC', i)])
    for n in ('LINK_RX', 'LINK_TX'):
        sh.wire(ep[n], es[n])
        sh.label((ep[n][0] + 3.81, ep[n][1]), n)
    for n in ('S3_EN', 'S3_TXD', 'S3_RXD', 'S3_IO0'):
        sh.wire(es[n], us[n])
        sh.label((es[n][0] + 3.81, es[n][1]), n)
    c = ep['CART_VCC']
    sh.wire(c, (99.06, c[1]), (99.06, pw['CART_VCC'][1]), pw['CART_VCC'])
    sh.label((c[0] + 3.81, c[1]), 'CART_VCC')
    sh.text((30.48, 139.7), NOTES, 1.524)
    return sh


NOTES = """FujiNet Pocket Rev0 (DRAFT, schematic only).  A FujiNet for the Analogue Pocket's cartridge slot: the openFPGA-7800
core serves the 7800 FujiNet mailbox and sends each request as a FujiBus packet in a SLIP frame at 115,200 baud 8N1 on
cartridge pin 5 (its TX), and listens on pin 31.  The board is the FujiNet half alone: ESP32-S3 (fujinet-firmware's RS232
build on UART1, pin map firmware/pocket.h), microSD, USB-C / CP2102N for flashing, its own LiPo.
Slot -> two Ioff buffers -> ESP32-S3 -> USB bridge; power: USB charges the cell and runs the board, the cell runs it
otherwise; the 3.3 V buck-boost runs while the Pocket's cart rail or USB is up.  The shell's lower corner must be GBA-shaped
(the Pocket's voltage switch unpressed) so the slot stays at 3.3 V.
FujiNet half: FujiNet-7800-Rev0 (fujinet-hardware, CERN-OHL-W-2.0).  Edge geometry: Gekkio GB-CART32K-A (CC-BY-4.0)."""
