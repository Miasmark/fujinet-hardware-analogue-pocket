# Network cores for the FujiNet Pocket cart: scoping note

Draft, 2026-11-20. This note looks at what the cart could do beyond the openFPGA-7800 core. It
covers:

- a **net terminal core** (phase 1);
- a **text web browser core** (phase 2);
- an **"update cores" core** (verdict: not possible as a core today; see section 4).

No HDL or firmware exists for any of these yet. Anything marked **verify** has not been checked on
hardware or in Analogue's docs.

## 1. What every network core shares

**The cart.** Each core uses the same Rev0 board:

- an ESP32-S3 running FujiNet's RS232 build;
- FujiBus packets in SLIP frames;
- 115,200 baud 8N1;
- core TX on cart pin 5 and core RX on pin 31.

The core talks to FujiNet's network devices (`N1`-`N8`). Those already handle TCP, TELNET and
HTTP/HTTPS, including TLS, DNS and WiFi setup. So a core never needs a TCP/IP stack or TLS of its
own: it opens a URL such as `N:TELNET://host:23/` or `N:HTTPS://host/path`, then reads and writes
bytes.

**HDL to reuse:** openFPGA-7800's `src/fpga/core/fujinet_mailbox.sv`. It holds the cart-side UART,
the SLIP framing and the FujiBus packet layer, and it has run against fujinet-pc. A network core
replaces the 7800 mailbox with a small CPU interface.

**A soft CPU, not a hand-built state machine.**

- Terminal emulation (ANSI/VT100), HTML parsing and menus are far easier in C than in HDL.
- Each core would run a small RISC-V (PicoRV32 or VexRiscv), with:
  - BRAM for code;
  - the Pocket's SDRAM for buffers;
  - memory-mapped registers for the FujiNet link, the keyboard, the mouse and the screen.
- The Cyclone V in the Pocket has far more logic and block RAM than this needs.

**Firmware.**

- *Option A (recommended): the stock FujiNet RS232 firmware.* Nothing changes on the cart. The
  same cart runs the 7800 core and the network cores, and every FujiNet update reaches them.
- *Option B: a cart firmware of its own.* The ESP32 would do the terminal emulation or the HTML
  rendering itself and send ready screens. That makes the core trivial but forks the firmware.
  Keep it only for what the stock N: device can't do (section 3, images).

**Link speed.**

- 115,200 baud carries about 11 KB/s. That is plenty for a terminal, but slow for web pages.
- The board's buffers (74LVC1G34) and the S3's UART go well past 1 Mbaud.
- Raising the link to 921,600 or more needs:
  - a baud setting in the RS232 build (**verify** what fujinet-firmware already allows);
  - a matching divisor in the core;
  - a check at speed with the breakout cart (signal edges through the 100 R series resistors and
    the slot).

**Keyboard and mouse.** They come from the Dock, through Analogue's firmware 1.1 beta 6 or later:
the USB keyboard is controller 3 and the mouse is controller 4.

- **Keyboard: known.** The Intellivision core already decodes it (`src/fpga/core/intv_input.sv`):
  - it is controller 3 with type 4, `cont3_key[31:28] == 4`;
  - up to six held keys, as HID usage codes: four in `cont3_joy[31:0]`, one per byte, and two in
    `cont3_trig[15:0]`. On hardware (the input monitor core, 2026-11-21) the report's six slots
    are packed big-endian: keys 1-4 in `joy[31:24]`, `[23:16]`, `[15:8]`, `[7:0]`, keys 5 and 6
    in `trig[15:8]`, `[7:0]`. A decoder should scan all six bytes anyway (the Intellivision core
    does);
  - the HID modifier byte (Ctrl, Shift, Alt, GUI, left and right) in `cont3_key[15:8]`:
    **confirmed on hardware** (the input monitor core, 2026-11-21). Left Ctrl, Shift, Alt and GUI
    are bits 8-11, right 12-15, in the usual HID order; `cont3_key[7:0]` stayed 0.

  That core decodes one code per clock in an 8-clock round, after a whole-word toggle handshake
  across the clock domains. Both can be reused as they are. A terminal needs:
  - key-down and repeat events, found by comparing each round's six codes with the last round's;
  - typematic repeat;
  - a HID-to-ASCII/VT table, with a layout setting (US first).
- **Mouse: documented by the Atari ST core**, defgenx/openfpga-AtariST, `docs/input.md`. Only
  the facts are taken here, in this note's words; that core's code is GPL-3.0 and none of it is
  used.
  - It is controller 4, with type 5: `cont4_key[31:28] == 5`. (Keyboard type 4 on controller 3
    matches the Intellivision core.)
  - **Relative X motion:** `cont4_joy[15:0]`, 16 bits.
  - **Relative Y motion:** `cont4_trig[15:0]`, 16 bits.
  - **Buttons:** `cont4_joy[18:16]`, three bits.
  - **Report counter:** `cont4_key[15:0]`.
  - The ST core turns the motion into PS/2 IntelliMouse packets. Its README calls the Dock
    keyboard and mouse only lightly tested on hardware.
  - **Not stated there, so verify on hardware:**
    - whether X and Y are signed deltas per report or running totals, and which way is positive;
    - how the counter should be used: presumably, take the motion once each time it changes;
    - which button bit is left, right or middle;
    - whether there is a wheel.

    The test is to draw the three cont4 words as hex on screen in a test core, then move the mouse,
    press each button and turn the wheel.
  - Phase 1 doesn't need the mouse.
- **Keyboard modifier byte: settled.** The Intellivision core read it from `cont3_key[7:0]` and
  the ST core's doc gives `cont3_key[15:8]`. The input monitor core
  (github.com/Miasmark/openfpga-input-monitor) shows `[15:8]` is right, on a Dock with firmware
  of 2026-11: the Intellivision core's ECS Shift and Ctrl needed the fix.
- **Without a Dock:** an on-screen keyboard, built on the Intellivision core's `intv_osk_draw.sv`
  and `tools/osk.py` layout tool. On the handheld, the D-pad moves the cursor and A types.
  - The ECS layout there is 5 rows. A terminal wants a fuller one (Esc, Tab, Ctrl, arrows).
  - Shortcut buttons: Start opens or closes it, and holding a shoulder button gives Ctrl or Shift.

**Display.**

- An 80 x 25 text screen of 8 x 16 glyphs is 640 x 400. The Pocket's scaler takes it to the
  1600 x 1440 panel with letterbox bars.
- A 4:3 mode of 80 x 30 at 640 x 480 is the other choice.
- Smaller fonts (8 x 8, 80 x 50) suit the Dock on a TV, but not the handheld screen.

## 2. Phase 1: net terminal core

**Goal:** a terminal for BBSs, MUDs and shells, from the Pocket or the Dock.

**Scope:**
- **Connections:** TELNET and raw TCP, through `N:`. For SSH, **verify** whether fujinet-firmware's
  SSH protocol handler is in the ESP32-S3 RS232 build. Without it, SSH waits for a firmware change.
- **Emulation:** ANSI-BBS and VT100/VT102. That covers cursor movement, the erase commands, scroll
  regions, the 16 colours plus bold and reverse, and the CP437 font for BBS art.
- **Input:** the USB keyboard (section 1) or the on-screen keyboard. Arrow keys, function keys
  and Ctrl send VT sequences.
- **UI:** a dialling directory kept in a save file (`/Saves/<platform>/...`). Each entry holds a
  host, a port, an emulation and a charset. Status line: online state, host and link rate.
- **Upload and download:** later, if at all. XMODEM or ZMODEM could save to `/Saves/`, as
  sections 4 and 5 allow.
- **WiFi setup:** FujiNet's own CONFIG, or its web page, as for the 7800 core. The core could add
  a small setup screen later.

**Work, roughly in order:**
1. Core skeleton: the APF bridge, video at 640 x 400, the soft CPU, BRAM and SDRAM.
2. Port `fujinet_mailbox.sv`'s link as a CPU peripheral. Test it with fujinet-pc over a USB
   serial adapter on the cart pins, as was done for the 7800 core.
3. The keyboard peripheral, reusing the Intellivision decoder, plus the mouse test screen.
4. C firmware for the CPU: an N: client, a VT/ANSI parser and the screen.
5. The on-screen keyboard.
6. The dialling directory and settings.

**Risk: low to moderate.** Every piece has a model: the FujiNet link (openFPGA-7800), the
keyboard (Intellivision) and terminal emulators. The unknowns are SSH in the S3 build and the link
rate.

## 3. Phase 2: text web browser core

**Goal:** read the web, Gopher, and maybe Gemini, as a text browser like Lynx: no JavaScript, and
no modern page layout.

**Scope:**
- **Fetching:** HTTP and HTTPS through `N:` (FujiNet handles TLS and redirects). Gopher over
  plain TCP. For Gemini, **verify**: it needs TLS on a raw TCP stream, so check whether `N:`
  offers that.
- **Rendering:** HTML to wrapped text, on the core's CPU, out of SDRAM. It handles:
  - headings, paragraphs and lists;
  - links, numbered or highlighted;
  - simple forms (text fields, submit);
  - character entities and UTF-8 to the font.

  Pages above a size limit are cut off.
- **Navigation:** the mouse (once the details in section 1 are checked) or the keyboard or D-pad. Links,
  scrolling, back and forward, and bookmarks in a save file.
- **Images:** none at first. A later step could have the ESP32 decode a small image to a palette
  bitmap (section 1, option B).

**Limits to say plainly:**
- Many sites need JavaScript or block text browsers. Wikipedia, news "lite" pages, text-only
  sites and Gopher work well; banking, social media and logins mostly don't.
- At 115,200 baud a 100 KB page takes about 10 seconds. A faster link matters here more than
  anywhere.

**Risk: moderate.** The renderer is the most work, but it is ordinary C. The other unknowns are
the mouse details, the link rate and Gemini's TLS.

## 4. An "update cores" core

**The question:** could a core on the Pocket, with the cart for internet, do what the community
updater utilities do on a computer? Those utilities read a JSON inventory of openFPGA cores,
compare it with what is installed, and copy new `Cores/`, `Platforms/` and `Assets/` files to the
SD card.

**Verdict: not as a core, with the openFPGA API as documented.**

Analogue's host/target command reference (developer docs, "Host/Target Commands") gives a core
these file operations on the Pocket's SD card:

| Command | What it does |
|---|---|
| `0x0180` / `0x0184` | Data slot read / write: read or write a slot's file at an offset. |
| `0x0190` | Get the full path of a data slot's file. |
| `0x0192` | Open a new file into a data slot, with flags to create the file if it doesn't exist and to resize it. |

The doc limits `0x0192`:
- "Only assets or saves may be opened."
- They must be "within platform folders that are supported in core.json". Its examples are
  `/Assets/<platform>/common/...` and `/Saves/<platform>/common/...`.

Nothing reaches `/Cores/`, where the bitstreams and core definitions live, or `/Platforms/`. The
command list also has no directory listing, no delete and no rename.

This blocks three things:
- **Seeing what's installed:** a core can't read `/Cores/*/core.json` to learn the installed
  versions.
- **Installing:** it can't write a new `.rbf_r` or `core.json` into `/Cores/`.
- **Cleaning up:** it can't remove or rename old files.

This is deliberate sandboxing, and it is sensible: a core that could rewrite other cores could
brick a user's SD card. It would take a firmware feature from Analogue: an API, or a built-in
updater.

**What a core can do today:**
- **"What's new" viewer:**
  - fetch the same public inventory the computer utilities use, over HTTPS through the cart;
  - show each core's latest version and release date, newest first.

  The user compares the list with the Pocket's own core list. It can't mark which cores are out of
  date, since it can't see the installed versions. The list could be kept in a save file: the user
  ticks the cores they have, and the viewer flags updates for those. It's clumsy, but it's honest.
- **Its own assets:** a network core can download files into its own `/Assets/<its platform>/`.
  That suits phone books or a BBS list for the terminal, but not other cores' assets.
- **Release notes:** a reader for a core's release notes, the same text the updater utilities
  link to.

**Other routes, outside a core:** none through this cart.
- The cart's microSD belongs to the ESP32. It isn't the Pocket's SD card, and the cart can't
  reach the Pocket's card.
- The Pocket shows its SD card to nothing over the cartridge slot.

**If Analogue adds file access to `/Cores/` and `/Platforms/`** (watch new firmware for new target
commands):
- The download, unzip and checksum steps would run on the ESP32. The ESP32 would stream each
  verified file to the core, and the core would write it with the new commands.
- Each file would go to a temporary name first, then be renamed, so a power loss never leaves a
  half-written core.
- Updating the updater core itself would be the last step, after everything else.

## 5. Open questions

1. **Mouse details:** check controller 4 on hardware with the input monitor core (section 1).
   The layout is known from the Atari ST core; the sign of the motion, the button order and the
   wheel are not. (The keyboard's modifier byte is settled: `cont3_key[15:8]`.)
2. **Link rate:** which bauds the RS232 build accepts, and a check at speed through the slot.
3. **SSH and TLS-over-TCP** in the S3 RS232 build (sections 2 and 3).
4. **Save-file writes:** what data.json flags a dialling directory or bookmark file needs
   (nonvolatile, size), so the core can grow the file with `0x0192`'s resize flag.
5. **Repository:** each core gets its own repository (openFPGA cores ship one per author.core).
   That repository would take `fujinet_mailbox.sv` from openFPGA-7800, and the input decoder and
   on-screen keyboard from the Intellivision core.
