import digitalio
import board
import busio
import time
import adafruit_sdcard
import storage
import adafruit_dht
import adafruit_pcf8523
import gc
import analogio
from board import SCL, SDA
from adafruit_seesaw.seesaw import Seesaw


def initialize_LED(board_pin):
    LED = digitalio.DigitalInOut(board_pin)
    LED.direction = digitalio.Direction.OUTPUT
    return LED

def threshold_check(LED, value, threshold_low, threshold_high):
    if (value >= threshold_low) and (value <= threshold_high): 		
        LED.value = True
    else:
        LED.value = False
    return LED

def analog_voltage(adc):
    return adc.value / 65535 * adc.reference_voltage

def valve(LED, temperature, temp_high, light, light_high, moisture, moisture_low, moisture_high):
    if moisture <= moisture_high:
        LED.value = True
    elif (temperature >= temp_high) and (light >= light_high) and (moisture <= (moisture_high + 200)):
        LED.value = True
    else:
        LED.value = False
    return LED


gc.enable()
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D10)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")
i2c_bus = busio.I2C(SCL, SDA)
ss = Seesaw(i2c_bus, addr=0x36)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)
dht = adafruit_dht.DHT22(board.D5)
photocell = analogio.AnalogIn(board.A1)

white_led = initialize_LED(board.D12)
green_led = initialize_LED(board.D11)
blue_led = initialize_LED(board.D9)
yellow_led = initialize_LED(board.D6)
valve_led = initialize_LED(board.D13)
plant_name = 0
plant_dict = {'Roma': [15, 32, 60, 80, 300, 800, 40000, 55000],
    'Cherry': [15,29,60,70,400,800,32000,50000],
    'Heirloom': [15,32,60,80,400,800,40000,52000],
    'Cherokee': [15,32,60,80,400,800,30000,52000],
    'Brandywine': [15,32,60,80,400,800,35000,52000],
    'Better Boy': [15,32,60,80,400,800,40000,52000],
    'Hybrid': [12,32,60,70,400,800,40000,50000],
    'Jubilee': [12,30,60,80,400,800,31000,53000],
    }
plant_list = str(list(plant_dict.keys()))
plant_list = plant_list.strip("[")
plant_list = plant_list.strip("]")
plant_list = plant_list.replace("'", ' ')
print('What tomato would you like to water?')
print(plant_list)
while plant_name not in plant_dict:
    plant_name = input('Choose Tomato: ')
    if plant_name not in plant_dict:
        print('Enter tomato from the list: ')
    else:
        plant_parameters = plant_dict[plant_name]

temp_low = plant_parameters[0]
temp_high = plant_parameters[1]
humid_low = plant_parameters[2]
humid_high = plant_parameters[3]
moisture_low = plant_parameters[4]
moisture_high = plant_parameters[5]
light_low = plant_parameters[6]
light_high = plant_parameters[7]


fo = open('/sd/ project_results.txt', "w")
count = 0
try:
    while True:
        count = count + 1
        t = rtc.datetime
        temperature = dht.temperature
        humidity = dht.humidity
        light = photocell.value
        moisture = ss.moisture_read()
        volts = analog_voltage(photocell)
        white_led = threshold_check(white_led, temperature, temp_low, temp_high)
        green_led = threshold_check(green_led, humidity, humid_low, humid_high)
        blue_led = threshold_check(blue_led, moisture, moisture_low, moisture_high)
        yellow_led = threshold_check(yellow_led, light, light_low, light_high)
        valve_led = valve(valve_led, temperature, temp_high, light, light_high, moisture, moisture_low, moisture_high)

        if (blue_led == False) and (moisture <= moisture_high):
            valve_led.value = True
        else:
            if moisture >= moisture_high:
                pass
            elif green_led.value == False:
                valve_led.value = True
            else:
                valve_led.value = False
#Adalogger Data
        date = str(t.tm_mday) + '/' + str(t.tm_mon) + '/' + str(t.tm_year)
        times = str(t.tm_hour) + ':' + str(t.tm_min) + ':' + str(t.tm_sec)
        info = date + ',' + times + ',' + str(temperature) + ',' + str(humidity) + ',' + str(moisture) + ',' + str(light) + "\n "

        print(count, info)
        fo.write(info)
        time.sleep(2)
        gc.collect()

except KeyboardInterrupt:
    fo.close()
