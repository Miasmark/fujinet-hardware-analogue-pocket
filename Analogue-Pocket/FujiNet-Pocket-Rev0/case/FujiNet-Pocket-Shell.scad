// FujiNet Pocket Rev0 shell (DRAFT, parametric): front piece, battery lid, back plate
// ---------------------------------------------------------------------------------------------
// Built on case/board-anchors.scad, which tools/gen_pcb.py generates from the board, so the shell
// follows the board: change a measurement there (README, "Measure with the breakout cart"), re-run
// the layout, and re-render this file.
//
// How the board sits in the Pocket (from a Pocket in hand):
//   * the board's BACK (B.Cu, no parts) lies nearly flush against the Pocket inside the
//     cartridge recess (below slot_y): no shell there, the bare board slides on the Pocket;
//   * the COMPONENT side (F.Cu, the fingers' side) faces the recess's open side, covered only by
//     the Pocket's lip below lip_y: the front piece stays low there;
//   * on the left (pin 1's side) the board keeps the tab's width up to switch_notch's top, so the
//     shell's GBA-shaped corner clears the Pocket's voltage switch;
//   * the battery rides on the front piece's roof (the shelf), in a bay closed by the lid; its
//     leads go down through a slot to the two pads at cell_leads.
//
// Frame: X, Y = the KiCad board frame (mm, y down; the whole model is mirrored to +Y up at the
// end), Z = 0 at the board's back face, the board's front face at Z = pcb_t.
//
// Parts (part = ...):
//   "front"    over the component side: walls, roof / shelf, battery bay, bosses, windows.
//              Print roof-down (bay walls down), supports only under the USB-C / microSD windows.
//   "lid"      closes the battery bay (a plate with a locating lip), the label recess on its
//              face.  Print face-down.
//   "plungers" the two button plungers (S3 reset, S3 BOOT): a stem through a guide collar on
//              the roof, a flange under the roof that keeps it captive (fit it from inside before
//              the board goes in).  Print standing on the stem's foot; the flange's 0.9 mm
//              overhang needs no support.
//   "back"     over the back, above slot_y only.  Print outside-down.
//   "assembly" all of them around a board stand-in; "all" laid out to print.
// Fasteners: 4x M2 x 8 pan head from the back plate through the board into the front piece's
// bosses at the four holes above slot_y (self-tapping 1.7 mm pilots, or 3.2 mm for M2 heat-set
// inserts); the two holes inside the recess take the front piece's locating pins.
//
// DRAFT: the recess numbers it rests on are estimates (board-anchors.scad); print a blank and fit
// it before anything else.  CERN-OHL-W-2.0, FujiNet Pocket Rev0.

include <board-anchors.scad>

part = "assembly";

// ------------------------------------------------------------ parameters --
clr      = 0.3;     // board edge to the inside of a wall
wall     = 1.4;     // side walls
roof     = 0.8;     // the front piece's roof over the parts = the battery shelf
part_h   = 3.3;     // tallest part above the board's front (USB-C 3.2, ESP32-S3 module 3.1)
low_h    = 1.45;    // tallest part below lip_y (SOT-23-5 buffers)
low_clr  = 0.35;    // and its clearance under the low roof
cover_end = 142.5;  // the front piece stops here (board y): the fingers start at 143
swell    = 0.5;     // room over the cell for it to swell
bay_clr  = 0.6;     // cell to the bay's walls
bay_wall = 1.4;
lid_t    = 1.2;
label_inset = 1.5;  // the label recess on the lid's face: inset from the lid's edges
label_t  = 0.4;     // and its depth
lid_lip  = 1.0;     // the lid's locating lip down inside the bay
lid_lip_t = 0.8;
boss_d   = 5.0;     // bosses (the board keeps a 3 mm part-free ring round each hole)
pilot_d  = 1.7;     // M2 self-tap pilot; 3.2 for M2 heat-set inserts
pin_d    = 2.0;     // locating pins through the two holes inside the recess
screw_d  = 2.4;     // M2 clearance through the back plate
head_d   = 4.2;     // M2 pan head counterbore
head_h   = 1.4;
back_gap = 1.3;     // the back plate's standoff from the board: the USB-C legs stand ~1 mm proud
back_t   = 1.0;
back_end_clr = 1.0; // the back plate stops this far above slot_y
usb_win  = [9.6, 3.8];   // USB-C window in the west wall: along y, along z (from the board's front - 0.2)
sd_win   = [12.4, 2.6];  // microSD window in the east wall
led_d    = 1.6;     // light-pipe holes over the three LEDs (1.5 mm acrylic rod / end-glow fibre)
// button plungers: TS-1187A, 1.5 mm above the board's front, ~0.25 mm travel
sw_h      = 1.5;
press_gap = 0.15;   // the stem above the switch at rest
stem_d    = 2.2;
stem_hole = 2.5;    // through the roof and the guide collar
flange_d  = 4.0;    // under the roof: the plunger is captive
flange_t  = 0.6;
collar_d  = 4.2;    // guide collar on the roof
collar_h  = 1.0;
proud     = 0.6;    // the stem's top above the collar at rest
lead_slot = [12, 2.4];   // the cell's lead slot through the shelf (x, y), at the cell's lower end

$fn = 40;
eps = 0.01;

// ---------------------------------------------------------- derived --------
z_f        = pcb_t;                          // board front face
roof_top   = pcb_t + shelf_z;                // the shelf the cell sits on
roof_bot   = roof_top - roof;
low_bot    = z_f + low_h + low_clr;
low_top    = low_bot + roof;
bay_top    = roof_top + cell_t + swell;      // the lid rests here
bay_in     = [cell[0] - bay_clr, cell[1] - bay_clr, cell[2] + bay_clr, cell[3] + bay_clr];
bay_out    = [bay_in[0] - bay_wall, bay_in[1] - bay_wall, bay_in[2] + bay_wall, bay_in[3] + bay_wall];
back_y_end = slot_y - back_end_clr;
screw_holes = [for (h = pcb_holes) if (h[1] < slot_y) h];
pin_holes   = [for (h = pcb_holes) if (h[1] >= slot_y) h];
assert(roof_bot - z_f >= part_h, "the shelf's underside must clear the tallest part");
assert(roof_bot - flange_t - 0.1 > z_f + sw_h + press_gap, "the plunger's flange must sit above its stem's foot");

// ---------------------------------------------------------- 2D shapes -------
module board2d() { polygon(pcb_outline); }
module band(y0, y1) { translate([0, y0]) square([300, y1 - y0]); }   // a horizontal band (board y)
module rect2d(r) { translate([r[0], r[1]]) square([r[2] - r[0], r[3] - r[1]]); }
module outer2d() { offset(r = clr + wall) board2d(); }
module inner2d() { offset(delta = clr) board2d(); }

// ---------------------------------------------------------- the front -------
module front() {
    difference() {
        union() {
            // upper body: walls from the board's back up to the roof, above lip_y
            linear_extrude(roof_top) intersection() { outer2d(); band(0, lip_y); }
            // low band under the Pocket's lip, down to cover_end
            linear_extrude(low_top) intersection() { outer2d(); band(lip_y - eps, cover_end); }
            // the battery bay's walls on the roof
            translate([0, 0, roof_top - eps]) linear_extrude(bay_top - roof_top + eps)
                difference() { rect2d(bay_out); rect2d(bay_in); }
        }
        // the cavity over the parts
        translate([0, 0, -eps]) linear_extrude(roof_bot + eps) intersection() { inner2d(); band(0, lip_y); }
        translate([0, 0, -eps]) linear_extrude(low_bot + eps) intersection() { inner2d(); band(lip_y - 1, cover_end + 1); }
        // windows: USB-C (west), microSD (east)
        translate([usb_c[0] - 5, usb_c[1] - usb_win[0] / 2, z_f - 0.2]) cube([8, usb_win[0], usb_win[1]]);
        translate([microsd[0] - 3, microsd[1] - sd_win[0] / 2, z_f - 0.2]) cube([8, sd_win[0], sd_win[1]]);
        // button plunger holes (through the roof and its guide collar), LED light-pipe holes
        for (p = [sw_s3_en, sw_s3_boot]) translate([p[0], p[1], roof_bot - 1]) cylinder(d = stem_hole, h = roof + collar_h + 2);
        for (p = [led_wifi, led_bus, led_charge]) translate([p[0], p[1], roof_bot - 1]) cylinder(d = led_d, h = roof + 2);
        // the cell's lead slot, at the bay's lower end over the pads
        translate([cell_leads[0] - lead_slot[0] / 2, bay_in[3] - lead_slot[1], roof_bot - 1])
            cube([lead_slot[0], lead_slot[1], roof + 2]);
    }
    // guide collars on the roof round the plunger holes
    for (p = [sw_s3_en, sw_s3_boot]) translate([p[0], p[1], roof_top - eps])
        difference() { cylinder(d = collar_d, h = collar_h + eps); translate([0, 0, -1]) cylinder(d = stem_hole, h = collar_h + 2); }
    // bosses down to the board's front: screw pilots above slot_y, locating pins inside the recess
    for (h = screw_holes) translate([h[0], h[1], z_f])
        difference() {
            cylinder(d = boss_d, h = roof_bot - z_f + eps);
            translate([0, 0, -eps]) cylinder(d = pilot_d, h = roof_bot);
        }
    for (h = pin_holes) translate([h[0], h[1], 0]) {
        translate([0, 0, z_f]) cylinder(d = boss_d, h = roof_bot - z_f + eps);
        cylinder(d = pin_d, h = z_f + eps);          // through the board, flush with its back
    }
}

// ---------------------------------------------------------- the lid ---------
module lid() {
    translate([0, 0, bay_top]) {
        difference() {
            linear_extrude(lid_t) rect2d(bay_out);
            translate([0, 0, lid_t - label_t]) linear_extrude(label_t + eps) offset(delta = -label_inset) rect2d(bay_out);
        }
        translate([0, 0, -lid_lip]) linear_extrude(lid_lip + eps)
            difference() {
                offset(delta = -0.15) rect2d(bay_in);
                offset(delta = -0.15 - lid_lip_t) rect2d(bay_in);
            }
    }
}

// ---------------------------------------------------------- the plungers ----
// One plunger, built standing on the board's front at the switch: stem from just above the switch
// up through the roof and collar to `proud` above it, flange just under the roof.
plunger_z0 = z_f + sw_h + press_gap;
plunger_top = roof_top + collar_h + proud;
module plunger() {
    translate([0, 0, plunger_z0]) cylinder(d = stem_d, h = plunger_top - plunger_z0);
    translate([0, 0, roof_bot - flange_t - 0.1]) cylinder(d = flange_d, h = flange_t);
}
module plungers() { for (p = [sw_s3_en, sw_s3_boot]) translate([p[0], p[1], 0]) plunger(); }

// ---------------------------------------------------------- the back --------
module back() {
    z0 = -(back_gap + back_t);
    difference() {
        union() {
            translate([0, 0, z0]) linear_extrude(back_t) intersection() { outer2d(); band(0, back_y_end); }
            // rim under the walls, and bosses at the screw holes
            translate([0, 0, -back_gap]) linear_extrude(back_gap)
                intersection() { difference() { outer2d(); inner2d(); } band(0, back_y_end); }
            for (h = screw_holes) translate([h[0], h[1], -back_gap]) cylinder(d = boss_d, h = back_gap);
        }
        for (h = screw_holes) translate([h[0], h[1], z0 - eps]) {
            cylinder(d = screw_d, h = back_gap + back_t + 2 * eps);
            cylinder(d = head_d, h = head_h);
        }
    }
}

// ---------------------------------------------------------- assembly ----------
module board_standin() {
    color("darkgreen") linear_extrude(pcb_t) board2d();
    color("silver") translate([cell[0], cell[1], roof_top]) cube([cell[2] - cell[0], cell[3] - cell[1], cell_t]);
}

mirror([0, 1, 0]) {
    if (part == "front") front();
    if (part == "lid") lid();
    if (part == "plungers") plungers();
    if (part == "back") back();
    if (part == "assembly") {
        board_standin();
        color("SteelBlue", 0.55) front();
        color("LightSteelBlue", 0.8) lid();
        color("OrangeRed") plungers();
        color("SlateGray", 0.8) back();
    }
    if (part == "all") {
        front();
        translate([70, 0, 0]) translate([0, 0, -bay_top]) lid();
        translate([140, 0, back_gap + back_t]) back();
        for (k = [0, 1]) translate([60 + 8 * k, -40, -plunger_z0]) plunger();
    }
}
