/* FujiNet Hardware Pin Mapping: FujiNet Pocket Rev0 (DRAFT)
 *
 * A FujiNet for the Analogue Pocket's cartridge slot (fujinet-hardware
 * Analogue-Pocket/FujiNet-Pocket-Rev0).  The Pocket's core is the cartridge: it serves
 * the console's FujiNet mailbox and sends each request as a FujiBus packet in a
 * SLIP frame at 115,200 baud 8N1 on cartridge pin 5, listening on pin 31.  This
 * board is the FujiNet half alone, on the generic RS232 build: UART1 is the
 * link (its presence selects the wired UART in lib/bus/rs232/rs232.h), through
 * two LVC buffers on the board.  Nothing here is console-specific.
 *
 * Proposed as include/pinmap/pocket.h; tools/check_pins.py in the board's
 * directory holds the schematic to this file.  SD and UART0 as
 * fujiversal-rs232.h.  Two plain LEDs, active low (led.cpp drives them high
 * at setup: off).  No buttons for keys.cpp: the board's two buttons are the
 * S3's EN and BOOT.  None of these GPIOs is a strapping pin (0, 3, 45, 46) or
 * the N16R8's octal PSRAM (35-37).
 */
#ifdef PINMAP_FUJINET_POCKET

/* SD Card - fnFsSD.cpp (the socket's detect switch is wired to IO42 but not
 * used until its polarity is checked on hardware) */
#define PIN_CARD_DETECT         GPIO_NUM_NC
#define PIN_CARD_DETECT_FIX     GPIO_NUM_NC
#define PIN_SD_HOST_CS          GPIO_NUM_41
#define PIN_SD_HOST_SCK         GPIO_NUM_39
#define PIN_SD_HOST_MISO        GPIO_NUM_40
#define PIN_SD_HOST_MOSI        GPIO_NUM_38

/* UART0: the CP2102N on USB-C (flashing, debug console) */
#define PIN_UART0_RX            GPIO_NUM_44
#define PIN_UART0_TX            GPIO_NUM_43

/* UART1: the link to the Pocket */
#define PIN_UART1_RX            GPIO_NUM_17 // (IN)  from cartridge pin 5, the core's TX
#define PIN_UART1_TX            GPIO_NUM_18 // (OUT) to cartridge pin 31, the core's RX
#define PIN_BUS_UART            UART_NUM_1

/* No modem control lines on this link */
#define PIN_RS232_RI            GPIO_NUM_NC
#define PIN_RS232_DCD           GPIO_NUM_NC
#define PIN_RS232_RTS           GPIO_NUM_NC
#define PIN_RS232_CTS           GPIO_NUM_NC
#define PIN_RS232_DTR           GPIO_NUM_NC
#define PIN_RS232_DSR           GPIO_NUM_NC
#define PIN_RS232_INVALID       GPIO_NUM_NC

/* Buttons - keys.cpp (common.h would put C on GPIO14, this board's WiFi LED) */
#define PIN_BUTTON_A            GPIO_NUM_NC
#define PIN_BUTTON_B            GPIO_NUM_NC
#define PIN_BUTTON_C            GPIO_NUM_NC

/* LEDs - led.cpp, active low */
#define PIN_LED_WIFI            GPIO_NUM_14
#define PIN_LED_BUS             GPIO_NUM_16
#define PIN_LED_BT              GPIO_NUM_NC

/* No audio output */
#define PIN_DAC1                GPIO_NUM_NC

#endif /* PINMAP_FUJINET_POCKET */
