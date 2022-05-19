from flask import request, Flask
import requests
#from multiprocessing import Pool
import multiprocessing
import threading
import json
from flask_api import FlaskAPI
from flask_cors import CORS
import RPi.GPIO as GPIO
import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from time import sleep


GPIO.cleanup()
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT)  # verde
GPIO.setup(11, GPIO.OUT)  # amarillo
GPIO.setup(13, GPIO.OUT)  # rojo
GPIO.setup(8, GPIO.IN)

GPIO.setup(29, GPIO.OUT)  # Verde
GPIO.setup(36, GPIO.OUT)  # amarillo
GPIO.setup(33, GPIO.OUT)  # rojo
GPIO.setup(10, GPIO.IN)


app = Flask(__name__)
CORS(app)


# class Semaforo(threading.Thread):
class Semaforo:

    def __init__(self, gpio1, gpio2, gpio3, freq):
        self.gpio1 = gpio1
        self.gpio2 = gpio2
        self.gpio3 = gpio3
        self.freq = freq
        self.start = True
        self.status = 'ON'

    def start_stoplight(self):
        while self.start:
            if self.status == 'ON':

                GPIO.output(self.gpio1, True)
                GPIO.output(self.gpio2, False)
                GPIO.output(self.gpio3, False)
                time.sleep(self.freq)

                GPIO.output(self.gpio1, False)
                GPIO.output(self.gpio2, True)
                GPIO.output(self.gpio3, False)
                time.sleep(self.freq)

                GPIO.output(self.gpio1, False)
                GPIO.output(self.gpio2, False)
                GPIO.output(self.gpio3, True)
                time.sleep(self.freq)

            elif self.status == 'OFF':

                GPIO.output(self.gpio1, False)
                GPIO.output(self.gpio2, False)
                GPIO.output(self.gpio3, False)
            else:

                GPIO.output(self.gpio1, False)
                GPIO.output(self.gpio2, True)
                GPIO.output(self.gpio3, False)
                time.sleep(self.freq)
                GPIO.output(self.gpio2, False)
                time.sleep(self.freq)

    def startCall(self):
        self.status = 'ON'
        return "All ok"

    def stopCall(self):
        self.status = 'OFF'
        return "All ok"

    def warningCall(self):
        self.status = 'WARNING'
        return "All ok"

    def changeFreqCall(self, freq):
        self.freq = freq
        return "All ok"

    def tarjetaWarning(self, sem1, sem2):
        reader = SimpleMFRC522()
        while True:
            id, text = reader.read()
            sleep(2)
            if id == 13328459841:

                print('leyendo')

                sem1.warningCall()
                sem2.warningCall()
                print(id)
                print(text)

    def tarjetaAPI(self,sem1,sem2):
        reader = SimpleMFRC522()
                
        while True:
            
            id, text = reader.read()
            print(id)
            print(text)
            parseo = str(id)
            headers = {'Content-type':'application/json'}
            dic = {"clave": parseo, "valor": text}
            url = 'http://wmeterws.pro2umanizales.com:6060/register'
            print(url)
            print(json.dumps(dic))
            req = requests.post(url,data=json.dumps(dic),headers=headers)
            print(req.status_code)
            
            
                
            

    def pulsador1(self):
        while True:
            if GPIO.input(8) == GPIO.HIGH:
                GPIO.output(13, True)
                GPIO.output(11, False)
                GPIO.output(37, False)

    def pulsador2(self):
        while True:
            if GPIO.input(10):
                GPIO.output(33, True)
                GPIO.output(36, False)
                GPIO.output(29, False)


def sync_stoplights(red1, green1, yellow1, red2, green2, yellow2, freq):
    while True:

        # enciendo rojo sem2
        GPIO.output(green2, False)
        GPIO.output(yellow2, False)
        GPIO.output(red2, True)
        time.sleep(freq)

        GPIO.output(green1, False)
        GPIO.output(yellow1, True)
        GPIO.output(red1, False)
        time.sleep(freq)

        GPIO.output(green1, True)
        GPIO.output(yellow1, False)
        GPIO.output(red1, False)
        time.sleep(freq)

        GPIO.output(green1, False)
        GPIO.output(yellow1, True)
        GPIO.output(red1, False)
        time.sleep(freq)

        GPIO.output(green1, False)
        GPIO.output(yellow1, False)
        GPIO.output(red1, True)

        GPIO.output(green2, False)
        GPIO.output(yellow2, True)
        GPIO.output(red2, False)
        time.sleep(freq)

        GPIO.output(green2, True)
        GPIO.output(yellow2, False)
        GPIO.output(red2, False)
        time.sleep(freq)

        GPIO.output(green2, False)
        GPIO.output(yellow2, True)
        GPIO.output(red2, False)
        time.sleep(freq)

        GPIO.output(green2, False)
        GPIO.output(yellow2, False)
        GPIO.output(red2, True)
        time.sleep(freq)


hilo_sincrono = threading.Thread(
    target=sync_stoplights, args=(13, 37, 11, 33, 29, 36, 3))

sem1 = Semaforo(37, 13, 11, 2)
sem2 = Semaforo(29, 36, 33, 2)


def start(sem):
    sem.startCall()


hilo1 = threading.Thread(target=sem1.start_stoplight, args=())
hilo2 = threading.Thread(target=sem2.start_stoplight, args=())
hilo3 = threading.Thread(target=sem1.tarjetaWarning, args=(sem1, sem2))
hilo4 = threading.Thread(target=sem1.tarjetaAPI, args=(sem1, sem2))
hilo_pulsador1 = threading.Thread(target=sem1.pulsador1, args=())
hilo_pulsador2 = threading.Thread(target=sem2.pulsador2, args=())


@app.route('/start_hilos/', methods=["GET"])
def start_all_hilos():
    hilo1.start()
    hilo2.start()
    hilo4.start()
    return 'inicio hilo'


@app.route('/start/', methods=["GET"])
def start_all():
    start(sem1)
    start(sem2)
    return 'todo esta correcti'


@app.route('/start/<sem>', methods=["GET"])
def start_one(sem):
    if sem == 'sem1':
        sem1.status = 'ON'

    elif sem == 'sem2':
        sem2.status = 'ON'

    return "MESSAGE PRENDIO SEM "


@app.route('/stop', methods=["GET"])
def stop_all():
    sem1.status = 'OFF'
    sem2.status = 'OFF'
    return "MESSAGE APAGO"


@app.route('/stop/<sem>', methods=["GET"])
def stop_one(sem):
    if sem == "sem1":
        sem1.status = 'OFF'

    if sem == "sem2":
        sem2.status = 'OFF'

    return "MESSAGE APAGO"


@app.route('/warning', methods=["GET"])
def warning_all():

    sem1.warningCall()
    sem2.warningCall()
    return "MESSAGE WARNING"


@app.route('/warning/<sem>', methods=["GET"])
def warning_one(sem):
    if sem == "sem1":
        sem1.warningCall()

    if sem == "sem2":
        sem2.warningCall()

    return "MESSAGE WARNING"


@app.route('/frecuencia/<freq>', methods=["GET"])
def change_freq_all(freq):
    freq = int(freq)
    sem1.changeFreqCall(freq)
    sem2.changeFreqCall(freq)
    return 'cambio'


@app.route('/<freq>/<sem>', methods=["GET"])
def change_freq(freq, sem):
    freq = int(freq)
    if sem == "sem1":
        sem1.changeFreqCall(freq)

    if sem == "sem2":
        sem2.changeFreqCall(freq)

    return 'cambio'


@app.route('/sync', methods=["POST"])
def sync():
    # hilo1.terminate()
    # hilo2.terminate()
    hilo_sincrono.start()
    return 'cambio'


@app.route('/tarjeta', methods=["POST"])
def tarjetapower():
    # hilo1.terminate()
    # hilo2.terminate()
    hilo3.start()
    return 'tarjeta'


@app.route('/pulsadores', methods=["POST"])
def pulsadorespower():
    # hilo1.terminate()
    # hilo2.terminate()
    hilo_pulsador1.start()
    hilo_pulsador2.start()
    return 'pulsador'


if __name__ == '__main__':
    app.run()
