import RPi.GPIO as GPIO
import time
import sqlite3
from datetime import datetime
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback
import threading

# query database parking_data.db:
# sqlite3 parking_data.db
# SELECT * FROM parking_log;

# Set up PubNub
pnconfig = PNConfiguration()
pnconfig.publish_key = "pub-c-c58b42a3-351f-4bd8-917e-8cf2b98951fa"
pnconfig.subscribe_key = "sub-c-f1db718c-3ec9-4cbe-a570-db64815a2e8b"
pnconfig.uuid = "userId"

# Current channel for real-time data
channel_current = "parking.current"

# History channel for history data
channel_history = "parking.history"

# Request channel for request data
channel_request = "parking.request"

pubnub = PubNub(pnconfig)

# GPIO setup
GPIO.setmode(GPIO.BCM)
TRIG_PIN = 23
ECHO_PIN = 24
RED_LED = 17
YELLOW_LED = 27
GREEN_LED = 22

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
    return pulse_duration * 34300 / 2

def turn_off_all_leds():
    GPIO.output(RED_LED, GPIO.LOW)
    GPIO.output(YELLOW_LED, GPIO.LOW)
    GPIO.output(GREEN_LED, GPIO.LOW)

def save_to_db(distance, led_status, timestamp):
    conn = sqlite3.connect("parking_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parking_log (timestamp, distance, led_status)
        VALUES (?, ?, ?)""", (timestamp, distance, led_status))
    conn.commit()
    conn.close()

def publish_current(distance, status):
    pubnub.publish().channel(channel_current).message({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "distance": distance,
        "led_status": status
    }).sync()

def publish_history():
    conn = sqlite3.connect("parking_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_log ORDER BY timestamp DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    history = [{
        "timestamp": row[1],
        "distance": row[2],
        "led_status": row[3]
    } for row in rows]

    pubnub.publish().channel(channel_history).message(history).sync()

class HistoryRequestListener(SubscribeCallback):
    def message(self, pubnub, message):
        if message.channel == channel_request:
            if message.message.get("command") == "history":
                publish_history()

pubnub.add_listener(HistoryRequestListener())
pubnub.subscribe().channels(channel_request).execute()

# Tracking LED state
previous_status = None

def monitor():
    global previous_status
    try:
        while True:
            distance = get_distance()
            print(f"Distance: {distance:.2f} cm")
            turn_off_all_leds()

            if distance > 50:
                current_status = "green"
                GPIO.output(GREEN_LED, GPIO.HIGH)
            elif 20 < distance <= 50:
                current_status = "yellow"
                GPIO.output(YELLOW_LED, GPIO.HIGH)
            else:
                current_status = "red"
                GPIO.output(RED_LED, GPIO.HIGH)

            # Publish current data
            publish_current(distance, current_status)

            # Log only on color change
            if current_status != previous_status:
                save_to_db(distance, current_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                previous_status = current_status

            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()

# Run monitoring in a thread so pubnub listener can also run
threading.Thread(target=monitor).start()
