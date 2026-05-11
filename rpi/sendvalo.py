import RPi.GPIO as IO
import sys
import time
from grove.adc import ADC
from numpy import interp
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

if (config["ADDRESS"] == None):
    print("no address found!")
    sys.exit(1)

IO.setwarnings(False)
IO.setmode(IO.BCM)

class GroveServo:
    MIN_DEGREE = 0
    MAX_DEGREE = 180
    INIT_DUTY = 2.5

    def __init__(self, channel):
        IO.setup(channel,IO.OUT)
        self.pwm = IO.PWM(channel,50)
        self.pwm.start(GroveServo.INIT_DUTY)

    def __del__(self):
        self.pwm.stop()

    def setAngle(self, angle):
        # Map angle from range 0 ~ 180 to range 25 ~ 125
        angle = max(min(angle, GroveServo.MAX_DEGREE), GroveServo.MIN_DEGREE)
        tmp = interp(angle, [0, 180], [25, 125])
        self.pwm.ChangeDutyCycle(round(tmp/10.0, 1))

class GroveLightSensor:

    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC(0x08)

    @property
    def light(self):
        value = self.adc.read(self.channel)
        return value


def main():

    sensor = GroveLightSensor(0)
    servo = GroveServo(12)

    kulmat = [x for x in range(0,181)]
    arvot = [0 for _ in kulmat]

    if (config["ADDRESS"] == None):
        print("no address found!")
        sys.exit(1)

    while True:
        for i in kulmat:
            servo.setAngle(i)
            time.sleep(0.01)
            arvot[i] = sensor.light
        c = zip(arvot, kulmat)
        c = sorted(c, key=lambda x: x[0])
        print(f"valo: {c[-1][0]}, angle: {c[-1][1]}")
        servo.setAngle(c[-1][1])
        measurements = {
            "light": c[-1][0],
            "angle": c[-1][1],
            "time": int(time.time())
        }

        r = requests.post(
            config["ADDRESS"],
            json=measurements,
            headers={"X-API-Token": config["API_TOKEN"]}
        )
        print(r.json())
        time.sleep(5)




if __name__ == "__main__":
    main()
