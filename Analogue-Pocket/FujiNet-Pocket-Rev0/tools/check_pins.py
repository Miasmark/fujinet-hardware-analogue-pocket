#!/usr/bin/env python3
"""The schematic against the firmware: design.py's ESP32-S3 nets against firmware/pocket.h (the pin
map this board proposes for fujinet-firmware), and the link path against what the openFPGA-7800
core expects on the Pocket's slot (pin 5 its TX, pin 31 its RX, pin 1 the rail).

Checks, each a hard failure:
  * every GPIO pocket.h names (UART0, UART1, SD, LEDs) is on the S3 pad design.py wires to that
    function's net, and no other pad carries that net;
  * no used GPIO is a strapping pin (0, 3, 45, 46 -- IO0 only as BOOT) or the N16R8's octal
    PSRAM (35-37);
  * slot pin 5 -> 100R -> the RX buffer's input; its output is UART1 RX; the RX buffer runs on +3V3;
  * UART1 TX -> the TX buffer's input; its output -> 100R -> slot pin 31; the TX buffer runs on the
    slot's rail (pin 1) and nothing else on that rail but its decoupling, the enable diode and pads.

Usage: python3 tools/check_pins.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
H = os.path.join(HERE, '..', 'firmware', 'pocket.h')

# pocket.h define -> the design.py net on that GPIO
WANT = {'PIN_UART0_RX': 'S3_RXD', 'PIN_UART0_TX': 'S3_TXD',
        'PIN_UART1_RX': 'LINK_RX', 'PIN_UART1_TX': 'LINK_TX',
        'PIN_SD_HOST_CS': 'SD_CS', 'PIN_SD_HOST_SCK': 'SD_SCK', 'PIN_SD_HOST_MISO': 'SD_MISO',
        'PIN_SD_HOST_MOSI': 'SD_MOSI', 'PIN_LED_WIFI': 'LED_WIFI', 'PIN_LED_BUS': 'LED_BUS'}
NC_REQUIRED = ['PIN_BUTTON_A', 'PIN_BUTTON_B', 'PIN_BUTTON_C', 'PIN_LED_BT', 'PIN_RS232_RTS', 'PIN_RS232_CTS',
               'PIN_RS232_DTR', 'PIN_RS232_DSR', 'PIN_RS232_DCD', 'PIN_RS232_RI']
STRAP, PSRAM = {3, 45, 46}, {35, 36, 37}
# the module's UART0 pads carry their own names in the symbol
PAD_GPIO = {'RXD0': 44, 'TXD0': 43}

bad = []


def fail(msg):
    bad.append(msg)


def main():
    src = open(H).read()
    defs = dict(re.findall(r'#define\s+(PIN_\w+)\s+(GPIO_NUM_\w+|UART_NUM_\d)', src))
    s3 = D.BY_KEY['U_S3']
    pad_fn = {}
    for fn, pad in D.S3_PAD.items():
        for p in (pad if isinstance(pad, list) else [pad]):
            pad_fn[str(p)] = fn
    gpio_net = {}
    for pad, net in s3.pins.items():
        fn = pad_fn[pad]
        g = PAD_GPIO.get(fn) if fn in PAD_GPIO else (int(fn[2:]) if fn.startswith('IO') else None)
        if g is not None:
            gpio_net[g] = net
    for name, net in WANT.items():
        v = defs.get(name)
        if not v or v == 'GPIO_NUM_NC':
            fail('%s missing or NC in pocket.h' % name)
            continue
        g = int(v.split('_')[-1])
        if gpio_net.get(g) != net:
            fail('%s = GPIO%d, but the schematic puts %s there (want %s)' % (name, g, gpio_net.get(g), net))
        others = [x for x, n in gpio_net.items() if n == net and x != g]
        if others:
            fail('%s also on GPIO %s' % (net, others))
        if g in STRAP or g in PSRAM:
            fail('%s = GPIO%d: a strapping / PSRAM pin' % (name, g))
    for name in NC_REQUIRED:
        if defs.get(name) != 'GPIO_NUM_NC':
            fail('%s must be GPIO_NUM_NC (got %s)' % (name, defs.get(name)))
    if defs.get('PIN_BUS_UART') != 'UART_NUM_1':
        fail('PIN_BUS_UART must be UART_NUM_1')
    for g, net in gpio_net.items():
        if net and (g in STRAP or g in PSRAM):
            fail('GPIO%d (strapping / PSRAM) carries %s' % (g, net))
    if gpio_net.get(0) != 'S3_IO0':
        fail('GPIO0 must be the BOOT net only')

    # the link path, part by part
    E = D.BY_KEY['J_EDGE'].pins
    if (E['1'], E['5'], E['31'], E['32']) != ('CART_VCC', 'POCKET_TX', 'POCKET_RX', 'GND'):
        fail('slot pins 1 / 5 / 31 / 32: %s' % [E[k] for k in ('1', '5', '31', '32')])
    if [n for k, n in E.items() if k not in ('1', '5', '31', '32') and n]:
        fail('slot pins other than 1, 5, 31, 32 are connected')
    rx, tx = D.BY_KEY['U_RXBUF'].pins, D.BY_KEY['U_TXBUF'].pins
    rin, rout = D.BY_KEY['R_RXIN'].pins, D.BY_KEY['R_TXOUT'].pins
    if set(rin.values()) != {'POCKET_TX', rx['2']}:
        fail('pin 5 does not reach the RX buffer through R_RXIN')
    if rx['4'] != 'LINK_RX' or rx['5'] != '+3V3':
        fail('RX buffer: Y %s, VCC %s' % (rx['4'], rx['5']))
    if tx['2'] != 'LINK_TX' or tx['5'] != 'CART_VCC':
        fail('TX buffer: A %s, VCC %s' % (tx['2'], tx['5']))
    if set(rout.values()) != {'POCKET_RX', tx['4']}:
        fail('the TX buffer does not reach pin 31 through R_TXOUT')
    on_rail = sorted(p.key for p in D.PARTS if 'CART_VCC' in p.pins.values())
    if on_rail != sorted(['J_EDGE', 'U_TXBUF', 'C_TXBUF', 'TP_CVCC', 'D_EN']):
        fail('CART_VCC (the Pocket\'s rail) feeds %s' % on_rail)

    if bad:
        raise SystemExit('check_pins:\n  ' + '\n  '.join(bad))
    print('check_pins: pocket.h and the link path match the schematic (%d GPIOs)' % len(WANT))


if __name__ == '__main__':
    main()
