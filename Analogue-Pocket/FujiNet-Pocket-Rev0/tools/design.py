"""FujiNet Pocket Rev0 -- the single source of truth.

A FujiNet for the Analogue Pocket's cartridge slot, as the openFPGA-7800 core
(2.2.7) uses it: the core serves the 7800 mailbox and sends FujiBus packets in
SLIP frames at 115,200 baud 8N1 on cartridge pins 5 (its TX) and 31 (its RX)
(openFPGA-7800 docs/FUJINET_POCKET_DEVICE.md).  This board is the FujiNet
half alone: an ESP32-S3 running fujinet-firmware's RS232 build on a wired
UART, microSD, USB-C with a CP2102N for flashing, its own LiPo.

Every part, value, footprint, MPN, manufacturer, LCSC code and pin->net
assignment lives here.  gen_sch.py and check_pins.py import it; the KiCad
files are generated output.  Parts are addressed by `key`; references are
numbered in declaration order, from the cartridge slot outward.

Provenance: tools and the FujiNet half (ESP32-S3, microSD, USB-C / CP2102N /
auto-program) from fujinet-hardware ATARI-7800/FujiNet-7800-Rev0 (itself the
NES / SMS Rev0 circuit), CERN-OHL-W-2.0.  The slot side, the LEDs and the
power sheet are new.  Firmware contract: firmware/pocket.h (the pin map this
board proposes for fujinet-firmware); tools/check_pins.py holds the netlist
to it.  Edge geometry: tools/make_edge_fp.py (from Gekkio's GB-CART32K-A,
CC-BY-4.0).

DRAFT (2026-11-20): schematic only, not laid out, not built.  New parts
without an LCSC code are marked lcsc='' and listed in README.md.
"""

LIB = 'FujiNet-Pocket'
PROJECT = 'FujiNet-Pocket-Rev0'
NC = None  # explicit no-connect

SHEETS = [  # (file stem, title, page) -- signal-flow order: the slot, the FujiNet, USB, power
    ('edge', 'Pocket cartridge slot, link buffers', 2),
    ('esp32s3-sd', 'ESP32-S3 FujiNet, microSD, LEDs', 3),
    ('usb-uart', 'USB-C, CP2102N bridge', 4),
    ('power', 'LiPo charger, power path, 3.3V buck-boost', 5),
]

# ESP32-S3-WROOM-1 module pad -> function (pads per the KiCad symbol)
S3_PAD = {'GND': [1, 40, 41], '3V3': 2, 'EN': 3, 'IO4': 4, 'IO5': 5, 'IO6': 6,
          'IO7': 7, 'IO15': 8, 'IO16': 9, 'IO17': 10, 'IO18': 11, 'IO8': 12,
          'IO19': 13, 'IO20': 14, 'IO3': 15, 'IO46': 16, 'IO9': 17, 'IO10': 18,
          'IO11': 19, 'IO12': 20, 'IO13': 21, 'IO14': 22, 'IO21': 23,
          'IO47': 24, 'IO48': 25, 'IO45': 26, 'IO0': 27, 'IO35': 28,
          'IO36': 29, 'IO37': 30, 'IO38': 31, 'IO39': 32, 'IO40': 33,
          'IO41': 34, 'IO42': 35, 'RXD0': 36, 'TXD0': 37, 'IO2': 38, 'IO1': 39}
# firmware/pocket.h.  SD and UART0 as fujiversal-rs232.h (the Freenove S3 map the
# 7800 and RS232 fujiversal builds share); UART1 is the link to the Pocket (its
# presence selects the wired UART in lib/bus/rs232/rs232.h); two plain LEDs,
# active low (lib/hardware/led.cpp drives them high = off at setup).  None of
# the chosen GPIOs is a strapping pin (0, 3, 45, 46) or the octal PSRAM's
# (35-37 on the N16R8).
S3_NET = {'EN': 'S3_EN', 'IO0': 'S3_IO0',
          'IO17': 'LINK_RX', 'IO18': 'LINK_TX',
          'IO38': 'SD_MOSI', 'IO39': 'SD_SCK', 'IO40': 'SD_MISO', 'IO41': 'SD_CS', 'IO42': 'SD_CD',
          'IO14': 'LED_WIFI', 'IO16': 'LED_BUS',
          'RXD0': 'S3_RXD', 'TXD0': 'S3_TXD'}

# The Pocket's cartridge slot, GB / GBC / GBA numbering (pin 1 VCC ... 32 GND).
# The core uses pin 5 (GBA /CS, GB /CS) as its TX, pin 31 (GBA /REQ, GB VIN) as
# its RX; pin 1 is the slot's rail, 3.3 V while the Pocket runs with cart power
# on (core.json cartridge_adapter 0).  Every other pin is left open, as
# Analogue's template leaves them (bank 0 an output held high, the rest inputs).
EDGE_NAMES = {1: 'VCC', 2: 'PHI', 3: '~{WR}', 4: '~{RD}', 5: '~{CS}'}
EDGE_NAMES.update({6 + i: 'A%d' % i for i in range(16)})
EDGE_NAMES.update({22 + i: 'D%d' % i for i in range(8)})
EDGE_NAMES.update({30: '~{RES}', 31: 'VIN/~{REQ}', 32: 'GND'})
EDGE = {p: NC for p in range(1, 33)}
EDGE.update({1: 'CART_VCC', 5: 'POCKET_TX', 31: 'POCKET_RX', 32: 'GND'})

# ---- common parts: (lib_id, footprint, MPN, LCSC) --------------------------
FP = lambda n: '%s:%s' % (LIB, n)
R0603 = FP('R_0603_1608Metric')
C0603 = FP('C_0603_1608Metric')
C0805 = FP('C_0805_2012Metric')
RES = {'100R': ('0603WAF1000T5E', 'C22775'), '330R': ('0603WAF3300T5E', 'C23138'),
       '1k': ('0603WAF1001T5E', 'C21190'), '4.7k': ('0603WAF4701T5E', 'C23162'),
       '5.1k': ('0603WAF5101T5E', 'C23186'), '10k': ('0603WAF1002T5E', 'C25804'),
       '22k': ('0603WAF2202T5E', 'C31850'), '47k': ('0603WAF4702T5E', 'C25819'),
       '100k': ('0603WAF1003T5E', 'C25803')}
CAP = {'100nF': (C0603, 'CC0603KRX7R9BB104', 'C14663'),
       '1uF': (C0603, 'CL10A105KB8NNNC', 'C15849'),
       '4.7uF': (C0603, 'CL10A475KO8NNNC', 'C19666'),
       '10uF': (C0603, 'CL10A106KP8NNNC', 'C19702'),
       '22uF': (C0805, 'CL21A226MAQNNNE', 'C45783')}
RPACK = {'4x10k': ('4D03WGJ0103T5E', 'C29718')}

# MPN -> manufacturer
MFR = {'CC0603KRX7R9BB104': 'YAGEO', 'CL10A106KP8NNNC': 'Samsung Electro-Mechanics',
       'CL10A475KO8NNNC': 'Samsung Electro-Mechanics', 'CL10A105KB8NNNC': 'Samsung Electro-Mechanics',
       'CL21A226MAQNNNE': 'Samsung Electro-Mechanics', 'TS-1187A-B-A-B': 'XKB Connection',
       'BAT54C,215': 'Nexperia', '4D03WGJ0103T5E': 'UNI-ROYAL', 'KT-0603R': 'Hubei KENTO Elec',
       'KT-0603G': 'Hubei KENTO Elec', 'ESP32-S3-WROOM-1-N16R8': 'Espressif', 'TF-015': 'SOFNG',
       'TYPE-C-31-M-12': 'Korean Hroparts Elec', 'ESD5Z5.0T1G': 'onsemi',
       'CP2102N-A02-GQFN28R': 'Silicon Labs', 'UMH3N': 'Jiangsu Changjing (JSCJ)',
       'AO3401A': 'Alpha & Omega Semiconductor', 'SS34': 'MDD (Microdiode Semiconductor)',
       'SN74LVC1G34DBVR': 'Texas Instruments', 'MCP73831T-2ACI/OT': 'Microchip',
       'TPS63001DRCR': 'Texas Instruments', 'SWPA4030S1R5NT': 'Sunlord',
       'S2B-PH-SM4-TB(LF)(SN)': 'JST'}
for _v in RES.values():
    MFR[_v[0]] = 'UNI-ROYAL'


class Part:
    def __init__(self, prefix, lib_id, value, footprint, pins, sheet,
                 mpn='', lcsc='', desc='', bom=True, dnp=False, ds='', key=None):
        self.prefix, self.lib_id, self.value, self.footprint = prefix, lib_id, value, footprint
        self.pins = {str(k): v for k, v in pins.items()}  # pad number -> net (None = NC)
        self.sheet, self.mpn, self.lcsc, self.desc, self.bom, self.dnp = sheet, mpn, lcsc, desc, bom, dnp
        self.mfr = MFR.get(mpn, '')
        self.nc_pads = ()
        self.ds = ds
        self.key = key
        self.ref = None


PARTS = []
_sheet = None


def sheet(name):
    global _sheet
    _sheet = name


def add(*a, **k):
    p = Part(*a, sheet=_sheet, **k)
    PARTS.append(p)
    return p


def R(value, a, b, desc='', **k):
    mpn, lcsc = RES[value]
    return add('R', 'Device:R', value, R0603, {1: a, 2: b}, mpn=mpn, lcsc=lcsc, desc=desc, **k)


def C(value, a, b='GND', desc='', **k):
    fp, mpn, lcsc = CAP[value]
    return add('C', 'Device:C', value, fp, {1: a, 2: b}, mpn=mpn, lcsc=lcsc, desc=desc, **k)


def RN(value, nets, common, desc='', **k):
    """4-resistor array: nets[0..3] on pins 1-4, common on 5-8."""
    mpn, lcsc = RPACK[value]
    pins = {i + 1: n for i, n in enumerate(nets)}
    pins.update({8 - i: common for i in range(4)})
    return add('RN', 'Device:R_Pack04', value, FP('R_Array_Convex_4x0603'), pins, mpn=mpn, lcsc=lcsc, desc=desc, **k)


def SW(value, net, desc, **k):
    return add('SW', 'Switch:SW_Push', value, FP('SW_SPST_TS-1187A'), {1: net, 2: 'GND'},
               mpn='TS-1187A-B-A-B', lcsc='C318884', desc=desc, **k)


def TP(net, label, desc='test pad', **k):
    return add('TP', 'Connector:TestPoint', label, FP('TestPoint_Pad_D1.5mm'), {1: net},
               desc=desc, bom=False, **k)


def LED(color, k_net, a_net, desc, **k):
    mpn, lcsc = {'red': ('KT-0603R', 'C2286'), 'green': ('KT-0603G', '')}[color]
    return add('D', 'Device:LED', color, FP('LED_0603_1608Metric'), {1: k_net, 2: a_net},
               mpn=mpn, lcsc=lcsc, desc=desc, **k)


def BUF(a, y, vcc, desc, **k):
    """SN74LVC1G34 single buffer, SOT-23-5 (DBV): 1 NC, 2 A, 3 GND, 4 Y, 5 VCC.  Ioff: with VCC
    at 0 V neither its input nor its output draws or sources current (partial power-down)."""
    return add('U', '74xGxx:74LVC1G34', '74LVC1G34', FP('SOT-23-5'), {1: NC, 2: a, 3: 'GND', 4: y, 5: vcc},
               mpn='SN74LVC1G34DBVR', lcsc='', desc=desc, **k)


# =========================================================================
sheet('edge')
add('J', '%s:Pocket_Cart_Edge_32' % LIB, 'Pocket_Cart_Edge_32', FP('Pocket_Cart_Edge_32'), EDGE,
    desc='Analogue Pocket cartridge slot (GB / GBA edge): 32 fingers at 1.5 mm, one face', bom=False,
    key='J_EDGE')
# Pocket -> device (pin 5, the core's TX): 100R at the finger, a buffer on the device's +3V3.
# With the device off (its battery flat) the buffer's Ioff input takes nothing from the Pocket;
# with the Pocket off the 100k holds the buffer's input low (a break, never a start bit train).
R('100R', 'POCKET_TX', 'RXB_IN', desc='link RX: series at the finger', key='R_RXIN')
R('100k', 'RXB_IN', 'GND', desc='link RX: defined low with the Pocket off', key='R_RXPD')
BUF('RXB_IN', 'LINK_RX', '+3V3', desc='link RX buffer on +3V3 (Pocket TX -> S3 UART1 RX)', key='U_RXBUF')
C('100nF', '+3V3', desc='RX buffer VCC', key='C_RXBUF')
# device -> Pocket (pin 31, the core's RX): a buffer powered from the slot's own rail (pin 1),
# so an unpowered Pocket never sees current from the device (Ioff on both sides of the buffer).
# The 100k holds its input low while the S3 is off: the core counts a line only once it has
# idled high for 1 ms, so a low pin 31 is never heard and the core stays on the link port.
R('100k', 'LINK_TX', 'GND', desc='link TX: defined low with the S3 off (the core ignores a low line)',
  key='R_TXPD')
BUF('LINK_TX', 'TXB_OUT', 'CART_VCC', desc='link TX buffer on the Pocket\'s cart rail (S3 UART1 TX -> Pocket RX)',
    key='U_TXBUF')
C('100nF', 'CART_VCC', desc='TX buffer VCC (the Pocket\'s rail)', key='C_TXBUF')
R('100R', 'POCKET_RX', 'TXB_OUT', desc='link TX: series at the finger', key='R_TXOUT')
TP('CART_VCC', 'CART_VCC', desc='bring-up: the Pocket\'s cart rail (pin 1)', key='TP_CVCC')
TP('POCKET_TX', 'P_TX', desc='bring-up: pin 5, the core\'s TX', key='TP_PTX')
TP('POCKET_RX', 'P_RX', desc='bring-up: pin 31, the core\'s RX', key='TP_PRX')
TP('GND', 'GND', desc='bring-up: scope ground by the link pads', key='TP_GNDE')

# =========================================================================
# The FujiNet half: the NES / SMS / 7800 Rev0 circuits.
sheet('esp32s3-sd')
s3 = {}
for fn, pad in S3_PAD.items():
    for p in (pad if isinstance(pad, list) else [pad]):
        s3[p] = 'GND' if fn == 'GND' else '+3V3' if fn == '3V3' else S3_NET.get(fn, NC)
add('U', 'RF_Module:ESP32-S3-WROOM-1', 'ESP32-S3-WROOM-1-N16R8', FP('ESP32-S3-WROOM-1'), s3,
    mpn='ESP32-S3-WROOM-1-N16R8', lcsc='C2913202', desc='FujiNet core (RS232 build, pocket pin map)', key='U_S3')
C('22uF', '+3V3', desc='S3 bulk (WiFi TX bursts)', key='C_S3BULK')
C('100nF', '+3V3', desc='S3 decoupling', key='C_S3')
R('10k', '+3V3', 'S3_EN', desc='EN pull-up', key='R_EN')
C('1uF', 'S3_EN', desc='EN power-on delay', key='C_EN')
SW('S3_RST', 'S3_EN', 'ESP32-S3 EN (reset)', key='SW_S3EN')
SW('S3_BOOT', 'S3_IO0', 'ESP32-S3 BOOT (IO0)', key='SW_S3BOOT')
add('J', '%s:MicroSD_TF015' % LIB, 'microSD', FP('TF-SMD_TF-015'),
    {1: 'SD_DAT2', 2: 'SD_CS', 3: 'SD_MOSI', 4: '+3V3', 5: 'SD_SCK', 6: 'GND',
     7: 'SD_MISO', 8: 'SD_DAT1', 9: 'SD_CD', 10: 'GND', 11: 'GND', 12: 'GND', 13: 'GND'},
    mpn='TF-015', lcsc='C113206', desc='microSD push-push, SPI mode', key='J_SD')
RN('4x10k', ['SD_CS', 'SD_MISO', 'SD_DAT1', 'SD_DAT2'], '+3V3', desc='SD pull-ups', key='RN_SD')
R('10k', '+3V3', 'SD_CD', desc='card-detect pull-up', key='R_SDCD')
C('10uF', '+3V3', desc='microSD supply', key='C_SD')
# status LEDs, active low from +3V3 (the WS2812 of the 7800 board needs 3.7 V or more; this board
# has no 5 V rail): WiFi (green) and bus activity (red)
R('1k', '+3V3', 'LED_WIFI_A', desc='WiFi LED series', key='R_LWIFI')
LED('green', 'LED_WIFI', 'LED_WIFI_A', desc='WiFi LED (IO14, low = on)', key='D_LWIFI')
R('1k', '+3V3', 'LED_BUS_A', desc='bus LED series', key='R_LBUS')
LED('red', 'LED_BUS', 'LED_BUS_A', desc='bus activity LED (IO16, low = on)', key='D_LBUS')

# =========================================================================
sheet('usb-uart')
add('J', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C', FP('USB_C_Receptacle_HRO_TYPE-C-31-M-12'),
    {'A1': 'GND', 'A4': 'VBUS', 'A5': 'CC1', 'A6': 'UBRG_DP', 'A7': 'UBRG_DM', 'A8': NC,
     'A9': 'VBUS', 'A12': 'GND', 'B1': 'GND', 'B4': 'VBUS', 'B5': 'CC2', 'B6': 'UBRG_DP',
     'B7': 'UBRG_DM', 'B8': NC, 'B9': 'VBUS', 'B12': 'GND', 'SH': 'GND'},
    mpn='TYPE-C-31-M-12', lcsc='C165948', desc='charging + S3 programming', key='J_USB')
R('5.1k', 'CC1', 'GND', desc='UFP Rd', key='R_CC1')
R('5.1k', 'CC2', 'GND', desc='UFP Rd', key='R_CC2')
for n, k in (('UBRG_DP', 'D_ESDP'), ('UBRG_DM', 'D_ESDM'), ('VBUS', 'D_ESDV')):
    add('D', 'Diode:ESD5Zxx', 'ESD5Z5.0T1G', FP('D_SOD-523'), {1: n, 2: 'GND'},
        mpn='ESD5Z5.0T1G', lcsc='C82044', desc='ESD', key=k)
C('1uF', 'VBUS', desc='VBUS decoupling at the connector', key='C_VBUS')
C('100nF', 'VBUS', desc='VBUS HF decoupling at the connector', key='C_VBUSHF')
cp = {i: NC for i in range(1, 30)}
cp.update({3: 'GND', 4: 'UBRG_DP', 5: 'UBRG_DM', 6: '+3V3', 7: '+3V3', 8: 'VBUS_SNS',
           9: 'CP_RST', 23: 'GND', 24: 'UART_RTS', 25: 'S3_TXD', 26: 'S3_RXD',
           28: 'UART_DTR', 29: 'GND'})
add('U', 'Interface_USB:CP2102N-Axx-xQFN28', 'CP2102N-A02-GQFN28', FP('QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm'),
    cp, mpn='CP2102N-A02-GQFN28R', lcsc='C964632', desc='USB-UART for S3 flashing/console (self-powered)',
    key='U_UART')
C('100nF', '+3V3', desc='CP2102N VDD', key='C_UART')
C('4.7uF', '+3V3', desc='CP2102N VDD bulk', key='C_UARTBULK')
R('22k', 'VBUS', 'VBUS_SNS', desc='VBUS sense divider', key='R_VBSH')
R('47k', 'VBUS_SNS', 'GND', desc='VBUS sense divider', key='R_VBSL')
R('10k', '+3V3', 'CP_RST', desc='/RST pull-up', key='R_CPRST')
add('U', 'Transistor_BJT:UMH3N', 'UMH3N', FP('SOT-363_SC-70-6'),
    {1: 'UART_RTS', 2: 'UART_DTR', 6: 'S3_EN', 3: 'S3_IO0', 4: 'UART_DTR', 5: 'UART_RTS'},
    mpn='UMH3N', lcsc='C62892', desc='esptool auto-program (DevKitC-1 style)', key='U_AUTOPROG')

# =========================================================================
sheet('power')
# The cell: a protected 1S LiPo pouch (a 303450 / 403450, 400-600 mAh) on a JST-PH.  Its own
# protection circuit is relied on; there is none on this board.  CHECK THE CELL'S POLARITY:
# JST-PH cells come wired both ways.
add('J', 'Connector_Generic:Conn_01x02', 'LiPo', FP('JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal'),
    {1: 'VBAT', 2: 'GND'}, mpn='S2B-PH-SM4-TB(LF)(SN)', lcsc='',
    desc='1S LiPo, protected cell: 1 +, 2 -', key='J_BAT')
# Charger: MCP73831-2 (4.20 V), I = 1000 V / R_PROG: 4.7k = 213 mA, about 0.5 C for 400 mAh.
add('U', 'Battery_Management:MCP73831-2-OT', 'MCP73831-2', FP('SOT-23-5'),
    {1: 'CHG_STAT', 2: 'GND', 3: 'VBAT', 4: 'VBUS', 5: 'CHG_PROG'},
    mpn='MCP73831T-2ACI/OT', lcsc='', desc='1S LiPo charger, 4.20 V, from USB only', key='U_CHG')
C('4.7uF', 'VBUS', desc='charger input', key='C_CHGIN')
C('4.7uF', 'VBAT', desc='charger output', key='C_CHGOUT')
R('4.7k', 'CHG_PROG', 'GND', desc='charge current 213 mA (1000 V / R)', key='R_PROG')
R('1k', 'VBUS', 'CHG_LED_A', desc='charge LED series', key='R_CHGLED')
LED('red', 'CHG_STAT', 'CHG_LED_A', desc='charging (STAT low)', key='D_CHG')
# Power path (Microchip AN1149, as the 7800 board's 5 V OR): USB VBUS through the SS34 onto VSYS;
# the cell through the AO3401A (G = VBUS, S = VSYS, D = VBAT), on without USB, off with it, so
# the charger charges the cell while USB runs the board.  4.7k holds the gate down against the
# SS34's reverse leakage, as on the 7800 board.
add('D', 'Diode:SS34', 'SS34', FP('D_SMA'), {1: 'VSYS', 2: 'VBUS'}, mpn='SS34', lcsc='C8678',
    desc='USB VBUS onto VSYS', key='D_VBUS')
add('Q', 'Transistor_FET:AO3401A', 'AO3401A', FP('SOT-23'), {1: 'VBUS', 2: 'VSYS', 3: 'VBAT'},
    mpn='AO3401A', lcsc='C15127', desc='cell onto VSYS without USB: G = VBUS, S = VSYS, D = VBAT', key='Q_BAT')
R('4.7k', 'VBUS', 'GND', desc='P-FET gate pull-down against the SS34 reverse leakage', key='R_VBPD')
# Enable: the Pocket's cart rail (it is on) or USB (charging, flashing) -- the board sleeps with
# the Pocket and needs no switch.  Pin 1 carries only this sense current (about 30 uA).
add('D', 'Diode:BAT54C', 'BAT54C', FP('SOT-23'), {1: 'CART_VCC', 2: 'VBUS', 3: 'PWR_EN'},
    mpn='BAT54C,215', lcsc='C37704', desc='PWR_EN = CART_VCC or VBUS, common cathode', key='D_EN')
R('100k', 'PWR_EN', 'GND', desc='PWR_EN low with the Pocket off and no USB', key='R_ENPD')
# 3.3 V: TPS63001 buck-boost (1.8-5.5 V in, 3.3 V fixed), so the S3 keeps 3.3 V over the cell's
# whole 3.0-4.2 V and through WiFi bursts.  PS/SYNC low: power-save mode at light load.  FB to
# VOUT on the fixed version.
C('22uF', 'VSYS', desc='buck-boost input', key='C_REGIN')
C('100nF', 'VSYS', desc='buck-boost VINA', key='C_VINA')
add('U', 'Regulator_Switching:TPS63001', 'TPS63001', FP('Texas_DRC0010J'),
    {1: '+3V3', 2: 'REG_L2', 3: 'GND', 4: 'REG_L1', 5: 'VSYS', 6: 'PWR_EN', 7: 'GND', 8: 'VSYS',
     9: 'GND', 10: '+3V3', 11: 'GND'},
    mpn='TPS63001DRCR', lcsc='', desc='3.3 V buck-boost, 1.2 A (buck) / 800 mA from 2.4 V (boost)', key='U_REG')
add('L', 'Device:L', '1.5uH', FP('L_Sunlord_SWPA4030S'), {1: 'REG_L1', 2: 'REG_L2'},
    mpn='SWPA4030S1R5NT', lcsc='', desc='buck-boost inductor (datasheet: 1.5 uH)', key='L_REG')
C('22uF', '+3V3', desc='buck-boost output', key='C_REGOUT1')
C('22uF', '+3V3', desc='buck-boost output', key='C_REGOUT2')
TP('VBAT', 'VBAT', desc='bring-up: the cell', key='TP_VBAT')
TP('VSYS', 'VSYS', desc='bring-up: the regulator input', key='TP_VSYS')
TP('+3V3', '+3V3', desc='bring-up: 3.3 V', key='TP_3V3')

# nets drawn as power symbols (global, never prefixed)
RAIL_NETS = ['GND', 'VBUS', 'VBAT', 'VSYS', '+3V3']

# ---- reference assignment (stable: declaration order) ---------------------
_count = {}
for p in PARTS:
    _count[p.prefix] = _count.get(p.prefix, 0) + 1
    p.ref = '%s%d' % (p.prefix, _count[p.prefix])

BY_REF = {p.ref: p for p in PARTS}
KEY = {p.key: p.ref for p in PARTS if p.key}
assert len(KEY) == len(PARTS), 'every part needs a unique key: %s' % sorted(
    p.ref for p in PARTS if not p.key)
BY_KEY = {p.key: p for p in PARTS}
assert [p.sheet for p in PARTS] == sorted((p.sheet for p in PARTS), key=[s[0] for s in SHEETS].index), \
    'parts must be declared sheet by sheet in SHEETS order'
assert all(p.mfr for p in PARTS if p.bom), 'manufacturer missing: %s' % [p.mpn for p in PARTS if p.bom and not p.mfr]


def nets():
    out = {}
    for p in PARTS:
        for pad, n in p.pins.items():
            if n:
                out.setdefault(n, []).append((p.ref, pad))
    return out


def sheet_nets():
    """net -> the set of sheets it has pins on."""
    out = {}
    for p in PARTS:
        for n in p.pins.values():
            if n:
                out.setdefault(n, set()).add(p.sheet)
    return out


if __name__ == '__main__':
    for p in PARTS:
        print(p.sheet, p.ref, p.key, p.value, p.footprint.split(':')[1], p.lcsc or '-', 'DNP' if p.dnp else '')
    ns = nets()
    print(len(PARTS), 'parts', len(ns), 'nets')
    for n, pp in sorted(ns.items()):
        if len(pp) < 2:
            print('SINGLE-PIN NET', n, pp)
    for n, ss in sorted(sheet_nets().items()):
        if len(ss) > 1 and n not in RAIL_NETS:
            print('CROSSES', n, sorted(ss))
