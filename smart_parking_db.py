import RPi.GPIO as GPIO
import time
import sqlite3
from datetime import datetime

# Set the GPIO mode (BCM or BOARD)
GPIO.setmode(GPIO.BCM)

# Define GPIO pins
TRIG_PIN = 23
ECHO_PIN = 24
RED_LED = 17     # Pin 11
YELLOW_LED = 27  # Pin 13
GREEN_LED = 22   # Pin 15

GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(YELLOW_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)

def get_distance():
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 34300 / 2
    return distance

def turn_off_all_leds():
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(YELLOW_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.LOW)

def save_to_db(distance, led_status):
    conn = sqlite3.connect("parking_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO parking_log (timestamp, distance, led_status) VALUES (?, ?, ?)", 
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), distance, led_status))
    conn.commit()
    conn.close()

# ✅ Track previous LED status
previous_status = None

try:
    while True:
        distance = get_distance()
        print(f"Distance: {distance:.2f} cm")

        turn_off_all_leds()

        # Determine current status
        if distance > 50:
            current_status = "green"
            GPIO.output(GREEN_LED, GPIO.HIGH)
        elif 20 < distance <= 50:
            current_status = "yellow"
            GPIO.output(YELLOW_LED, GPIO.HIGH)
        else:
            current_status = "red"
            GPIO.output(RED_LED, GPIO.HIGH)

        # ✅ Only log if status has changed
        if current_status != previous_status:
            save_to_db(distance, current_status)
            previous_status = current_status

        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()