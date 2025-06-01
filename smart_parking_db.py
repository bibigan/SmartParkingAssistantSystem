import RPi.GPIO as GPIO
import time
import sqlite3
from datetime import datetime

# query database parking_data.db
# sqlite3 parking_data.db
# SELECT * FROM parking_log;

# Set the GPIO mode (BCM or BOARD)
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for the ultrasonic sensor
TRIG_PIN = 23
ECHO_PIN = 24

# Define GPIO pins for the Traffic Light LED module
RED_LED = 17     # Pin 11
YELLOW_LED = 27  # Pin 13
GREEN_LED = 22   # Pin 15

# Set up ultrasonic sensor pins
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Set up LED pins
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(YELLOW_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)

def get_distance():
    # Send a short pulse to the trigger pin
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # Measure the duration for the echo pulse
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start

    # Calculate the distance based on the speed of sound (34300 cm/s)
    distance = pulse_duration * 34300 / 2
    return distance

def turn_off_all_leds():
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(YELLOW_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.LOW)

try:
    while True:
        distance = get_distance()
        print(f"Distance: {distance:.2f} cm")

        # Turn off all LEDs first
        turn_off_all_leds()

        # Control LEDs based on distance
        if distance > 50:
            GPIO.output(GREEN_LED, GPIO.HIGH)
            save_to_db(distance, "green")
        elif 20 < distance <= 50:
            GPIO.output(YELLOW_LED, GPIO.HIGH)
            save_to_db(distance, "yellow")
        else:
            GPIO.output(RED_LED, GPIO.HIGH)
            save_to_db(distance, "red")

        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()


def save_to_db(distance, led_status):
    conn = sqlite3.connect("parking_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO parking_log (timestamp, distance, led_status) VALUES (?, ?, ?)", 
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), distance, led_status))
    conn.commit()
    conn.close()