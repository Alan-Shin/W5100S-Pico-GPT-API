import board,busio, os
import adafruit_ili9341
import displayio
import time
import digitalio
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import bitmaptools
import traceback
import storage

try:
    storage.remount("/", False)

except Exception as e:
    print(f"Error remounting the filesystem: {e}")

try:
    ##SPI0
    SPI0_SCK = board.GP18
    SPI0_TX = board.GP19
    SPI0_RX = board.GP16
    SPI0_CSn = board.GP17

    ##reset
    W5x00_RSTn = board.GP20

    ##Resistor
    gp13 = digitalio.DigitalInOut(board.GP13)
    gp13.direction = digitalio.Direction.OUTPUT

    gp13.value = True

    button1 = digitalio.DigitalInOut(board.GP9)
    button2 = digitalio.DigitalInOut(board.GP8)
    button3 = digitalio.DigitalInOut(board.GP7)
    button4 = digitalio.DigitalInOut(board.GP6)
    button5 = digitalio.DigitalInOut(board.GP5)
    button1.direction = digitalio.Direction.INPUT
    button2.direction = digitalio.Direction.INPUT
    button3.direction = digitalio.Direction.INPUT
    button4.direction = digitalio.Direction.INPUT
    button5.direction = digitalio.Direction.INPUT
    button1.pull = digitalio.Pull.UP
    button2.pull = digitalio.Pull.UP
    button3.pull = digitalio.Pull.UP
    button4.pull = digitalio.Pull.UP
    button5.pull = digitalio.Pull.UP

    #print("Wiznet5k Loopback Test (DHCP)")
    # Setup your network configuration below
    # random MAC, later should change this value on your vendor ID
    MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
    IP_ADDRESS = (192, 168, 0, 50)
    SUBNET_MASK = (255, 255, 255, 0)
    GATEWAY_ADDRESS = (192, 168, 0, 1)
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
    #print("server listen")

    #print("Chip Version:", eth.chip)
    #print("MAC Address:", [hex(i) for i in eth.mac_address])
    #print("My IP address is:", eth.pretty_ip(eth.ip_address))

    # edit host and port to match server
    HOST = "192.168.0.4"
    PORT = 5000
    TIMEOUT = 5
    INTERVAL = 5
    MAXBUF = 2048

    #print("Create TCP Client Socket")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    #print("Connecting")
    s.connect((HOST, PORT))

    buf = b''
    len_buf = 0

    # 초기화
    # set gpio number
    mosi_pin, clk_pin, reset_pin, cs_pin, dc_pin = board.GP11, board.GP10, board.GP2, board.GP3, board.GP4
    #  releases all resources associated with any currently open displays
    displayio.release_displays()

    spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)

    display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

    display = adafruit_ili9341.ILI9341(display_bus, width=240, height=320, rotation=90)
    # print(f"display={display}")

    board_type = os.uname().machine
    #print(f"Board: {board_type}")


    while True: 
        while True:
            data = s.recv(MAXBUF)   
            if not data:             
                continue
            
            if len(data): 
                print(len(data))
                if not len_buf:
                    if b"LEN" in data:

                        len_buf = int(data.decode().split(":")[1])
                        print(f"length of buf = {len_buf}")
                else:
                    buf += data
                    if len(buf) >= len_buf:
                        break

        bmp_data = bytearray(buf)
        with open ("test.bmp", "wb") as f:
            f.write(bmp_data)
        f.close()

        group = displayio.Group()
        display.show(group)

        bitmap = displayio.OnDiskBitmap("/test.bmp")
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        group.append(tile_grid)

        os.remove("/test.bmp")

        while True:
            pressed = button1.value + button2.value * 2 + button3.value * 2 ** 2 + button4.value * 2 ** 3

            if pressed != 15 :
                break

        s.send(f"{15 - pressed}".encode())

        bmp_data = None
        buf = b''
        bitmap = None
        group.remove(tile_grid)
        tile_grid = None

        data = ''

        len_buf = 0
        while True:
            data = s.recv(MAXBUF)    # 최대 MAXBUF 바이트의 데이터를 수신
            if not data:             # 데이터가 없다면 계속 데이터를 수신받고있음
                continue
            
            if len(data): 
                #print(len(data))
                if not len_buf:
                    if b"LEN" in data:

                        len_buf = int(data.decode().split(":")[1])
                        #print(f"length of buf = {len_buf}")
                else:
                    buf += data
                    if len(buf) >= len_buf:
                        break
        #print(f'Received {len(buf)} bytes')

        board_type = os.uname().machine
        #print(f"Board: {board_type}")

        bmp_data = bytearray(buf)
        with open ("test2.bmp", "wb") as f:
            f.write(bmp_data)

        group = displayio.Group()
        display.show(group)

        bitmap = displayio.OnDiskBitmap("/test2.bmp")
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        group.append(tile_grid)
        time.sleep(10)

        # Card Description
        
        s.send(f"Card Description".encode())

        while True:
            data = s.recv(MAXBUF)    # 최대 MAXBUF 바이트의 데이터를 수신
            if not data:             # 데이터가 없다면 계속 데이터를 수신받고있음
                continue 
            print(f"{data.decode()}")
            s.send(b"OK")
            break
        #print(f"End")
        bmp_data = None
        buf = b''
        bitmap = None
        group.remove(tile_grid)
        tile_grid = None
        time.sleep(2)

        break
        
        
        while True:
            pressed = button5.value
            if pressed != 0:
                continue
            s.send("pushed")
            break

        continue
            #print(f"status={15 - pressed}")
            #print(f"button 1 status={button1.value}")
    s.close()


except Exception as e:
    print(f"ERROR:{e}")