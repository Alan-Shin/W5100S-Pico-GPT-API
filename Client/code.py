import board,busio, os
from time import sleep
import adafruit_ili9341
import displayio
import time
import digitalio
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import bitmaptools
import traceback
import storage


def extract_palette(bmp_data, color_depth=None):
    if not color_depth:
        color_depth = bmp_data[28]
    if color_depth not in [1, 4, 8, 16, 24, 32]:
        raise ValueError("Unsupported color depth")

    # Extract the color table from the BMP data (if applicable)
    if color_depth <= 8:
        color_table_offset = bmp_data[10] + 14
        color_table_size = 4 * 2 ** color_depth
        color_table_data = bmp_data[color_table_offset:color_table_offset+color_table_size]

        # Split the color table data into 4-byte color entries and insert them into a Palette
        palette = displayio.Palette(2 ** color_depth)
        for i in range(0, len(color_table_data), 4):
            color = (color_table_data[i+2], color_table_data[i+1], color_table_data[i], color_table_data[i+3])
            palette[i//4] = color

        return palette

    else:
        return None # no color table for 16, 24, or 32 bpp


def create_bitmap_from_bmp(bmp_data):
    # Extract the BMP header fields
    width = bmp_data[18] + (bmp_data[19] << 8)
    height = bmp_data[22] + (bmp_data[23] << 8)
    color_depth = bmp_data[28]

    # Create the Bitmap object with the appropriate color depth
    if color_depth == 1:
        bmp = displayio.Bitmap(width, height, 2)
    elif color_depth == 4:
        bmp = displayio.Bitmap(width, height, 16)
    elif color_depth == 8:
        bmp = displayio.Bitmap(width, height, 256)
    elif color_depth == 16:
        bmp = displayio.Bitmap(width, height, 65536)
    elif color_depth == 24:
        bmp = displayio.Bitmap(width, height, 16777216)
    elif color_depth == 32:
        bmp = displayio.Bitmap(width, height, 4294967296)
    else:
        raise ValueError("Unsupported color depth")

    # Extract the pixel data from the BMP data and insert it into the Bitmap
    pixel_data_offset = 40
    '''
        for y in range(height):
            for x in range(width):
                pixel_offset = pixel_data_offset + (height - y - 1) * width * (color_depth // 8) + x * (color_depth // 8)
                if color_depth == 1:
                    pixel = (bmp_data[pixel_offset >> 3] >> (7 - (pixel_offset & 7))) & 1
                elif color_depth == 4:
                    pixel = (bmp_data[pixel_offset >> 1] >> ((pixel_offset & 1) * 4)) & 0x0f
                elif color_depth == 8:
                    pixel = bmp_data[pixel_offset]
                elif color_depth == 16:
                    pixel = bmp_data[pixel_offset+1] << 8 | bmp_data[pixel_offset]
                elif color_depth == 24:
                    pixel = bmp_data[pixel_offset+2] << 16 | bmp_data[pixel_offset+1] << 8 | bmp_data[pixel_offset]
                elif color_depth == 32:
                    pixel = bmp_data[pixel_offset+3] << 24 | bmp_data[pixel_offset+2] << 16 | bmp_data[pixel_offset+1] << 8 | bmp_data[pixel_offset]
                    pixel = bmp_data
                bmp[x, y] = pixel

        return bmp
    '''
    for y in range(height):
        for x in range(width):
            pixel_offset = pixel_data_offset + (height - y - 1) * width * (color_depth // 8) + x * (color_depth // 8)
            if color_depth == 1:
                pixel = (bmp_data[pixel_offset >> 3] >> (7 - (pixel_offset & 7))) & 1
            elif color_depth == 4:
                pixel = (bmp_data[pixel_offset >> 1] >> ((pixel_offset & 1) * 4)) & 0x0f
            elif color_depth == 8:
                pixel = bmp_data[pixel_offset]
            elif color_depth == 16:
                pixel = bmp_data[pixel_offset+1] << 8 | bmp_data[pixel_offset]
            elif color_depth == 24:
                pixel = bmp_data[pixel_offset+2] << 16 | bmp_data[pixel_offset+1] << 8 | bmp_data[pixel_offset]
            elif color_depth == 32:
                pixel = bmp_data[pixel_offset+3] << 24 | bmp_data[pixel_offset+2] << 16 | bmp_data[pixel_offset+1] << 8 | bmp_data[pixel_offset]
            
            bmp[width - x - 1, y] = pixel  # 좌우 반전
            
    return bmp


try:
    storage.remount("/", False)
    ##SPI0
    SPI0_SCK = board.GP18
    SPI0_TX = board.GP19
    SPI0_RX = board.GP16
    SPI0_CSn = board.GP17

    ##reset
    W5x00_RSTn = board.GP20

    print("Wiznet5k Loopback Test (DHCP)")
    # Setup your network configuration below
    # random MAC, later should change this value on your vendor ID
    MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
    IP_ADDRESS = (192, 168, 7, 50)
    SUBNET_MASK = (255, 255, 255, 0)
    GATEWAY_ADDRESS = (192, 168, 7, 1)
    DNS_SERVER = (8, 8, 8, 8)

    led = digitalio.DigitalInOut(board.GP25)
    led.direction = digitalio.Direction.OUTPUT

    ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
    ethernetRst.direction = digitalio.Direction.OUTPUT

    # For Adafruit Ethernet FeatherWing
    cs = digitalio.DigitalInOut(SPI0_CSn)
    # For Particle Ethernet FeatherWing
    # cs = digitalio.DigitalInOut(board.D5)

    spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)

    # Reset W5x00 first
    ethernetRst.value = False
    time.sleep(1)
    ethernetRst.value = True

    # # Initialize ethernet interface without DHCP
    eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
    # # Set network configuration
    eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

    # Initialize ethernet interface with DHCP
    #eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)

    # Initialize a socket for our server
    socket.set_interface(eth)
    server = socket.socket()  # Allocate socket for the server
    server_ip = None  # IP address of server
    server_port = 5000  # Port to listen on
    server.bind((server_ip, server_port))  # Bind to IP and Port
    server.listen()  # Begin listening for incoming clients
    print("server listen")

    print("Chip Version:", eth.chip)
    print("MAC Address:", [hex(i) for i in eth.mac_address])
    print("My IP address is:", eth.pretty_ip(eth.ip_address))

    # edit host and port to match server
    HOST = "192.168.0.8"
    PORT = 5000
    TIMEOUT = 5
    INTERVAL = 5
    MAXBUF = 2048

    print("Create TCP Client Socket")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    print("Connecting")
    s.connect((HOST, PORT))

    buf = b''
    len_buf = 0
    while True:
        data = s.recv(MAXBUF)    # 최대 MAXBUF 바이트의 데이터를 수신
        if not data:             # 데이터가 없다면 계속 데이터를 수신받고있음
            continue
        
        if len(data):            # 
            print(len(data))
            if not len_buf:
                if b"LEN" in data:
                    # org=b'LEN:11078'
                    # str_data=b'LEN:11078'
                    # ["b'LEN", "11078'"]
                    # print(f"org={data}")
                    # str_data = data.decode()
                    # print(f"str_data={str_data}")
                    # print(str_data.split(":"))
                    len_buf = int(data.decode().split(":")[1])
                    # len_buf = 11078
                    print(f"length of buf = {len_buf}")
            else:
                buf += data
                if len(buf) >= len_buf:
                    break
    print(f'Received {len(buf)} bytes')

    board_type = os.uname().machine
    print(f"Board: {board_type}")

    # set gpio number
    mosi_pin, clk_pin, reset_pin, cs_pin, dc_pin = board.GP11, board.GP10, board.GP2, board.GP3, board.GP4

    #  releases all resources associated with any currently open displays
    displayio.release_displays()

    spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)

    display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

    display = adafruit_ili9341.ILI9341(display_bus, width=240, height=320, rotation=90)
    print(f"display={display}")
    # bitmap = displayio.OnDiskBitmap("/0.bmp")

    bmp_data = bytearray(buf)

    bmp = create_bitmap_from_bmp(bmp_data)
    palette = extract_palette(bmp_data)
    group = displayio.Group()
    display.show(group)

    tile_grid = displayio.TileGrid(bitmap=bmp, pixel_shader=palette)
    group.append(tile_grid)
    # display.show(bitmap)
    sleep(20)
except Exception as e:
    print(f"ERROR:{e}:{traceback.format_exc()}")