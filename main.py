from ov7670 import OV7670_30x40_RGB565 as CAM
import sys
import time
import digitalio
import busio
import board
import pwmio
from adafruit_ov7670 import (
    OV7670,
    OV7670_SIZE_DIV16,
    OV7670_COLOR_YUV,
)
import random

class Perceptron:
    def __init__(self, input_size, learning_rate=0.01): # Corregido: __init__
        self.weights = [random.uniform(-1, 1) for _ in range(input_size)]
        self.bias = random.uniform(-1, 1)
        self.learning_rate = learning_rate

    def predict(self, inputs):
        summation = sum(w * i for w, i in zip(self.weights, inputs)) + self.bias
        return 1 if summation >= 0 else 0

    def train(self, inputs, target):
        prediction = self.predict(inputs)
        error = target - prediction

        self.weights = [w + self.learning_rate * error * i for w, i in zip(self.weights, inputs)]
        self.bias += self.learning_rate * error


cam = CAM(
    d0_d7pinslist=[board.GP4, board.GP5, board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11],
    plk=board.GP12, xlk=board.GP13, sda=board.GP14, scl=board.GP15,
    hs=board.GP16, vs=board.GP17, ret=board.GP18, pwdn=board.GP19
)

motor_a_adelante = digitalio.DigitalInOut(board.GP20)
motor_a_atras = digitalio.DigitalInOut(board.GP21)
motor_b_adelante = digitalio.DigitalInOut(board.GP22)
motor_b_atras = digitalio.DigitalInOut(board.GP26)

for m in [motor_a_adelante, motor_a_atras, motor_b_adelante, motor_b_atras]:
    m.direction = digitalio.Direction.OUTPUT

enable_a = pwmio.PWMOut(board.GP27, frequency=1000)
enable_b = pwmio.PWMOut(board.GP0, frequency=1000)

cam.size = OV7670_SIZE_DIV16
cam.colorspace = OV7670_COLOR_YUV
cam.flip_y = True


def aplicar_motores(vel_a, vel_b, dir_a="fwd", dir_b="fwd"):

    motor_a_adelante.value = (dir_a == "fwd")
    motor_a_atras.value = (dir_a == "rev")

    motor_b_adelante.value = (dir_b == "fwd")
    motor_b_atras.value = (dir_b == "rev")
    enable_a.duty_cycle = int(65535 * max(0, min(1.0, vel_a)))
    enable_b.duty_cycle = int(65535 * max(0, min(1.0, vel_b)))

def detener():
    aplicar_motores(0, 0)

def detectar_centro_linea(buf, width, height, threshold):
    fila_analizar = height - 10 
    inicio_fila = 2 * width * fila_analizar
    fin_fila = inicio_fila + 2 * width
    
    suma_posiciones = 0
    conteo_negro = 0
    
    for x in range(width):
        y_val = buf[inicio_fila + (x * 2)]
        if y_val < threshold:
            suma_posiciones += x
            conteo_negro += 1

    return suma_posiciones // conteo_negro if conteo_negro > 0 else None

def ajustar_direccion(centro, width, perceptron, velocidad_actual, entrenar=False):
    centro_ideal = width // 2
    margen = width // 5
    desviacion = abs(centro - centro_ideal) / centro_ideal 
    
    inputs = [desviacion, velocidad_actual]
    
    if entrenar:
        target = 1 if desviacion < 0.2 else 0
        perceptron.train(inputs, target)
    if perceptron.predict(inputs) == 1:
        velocidad_actual = min(0.8, velocidad_actual + 0.05)
    else:
        velocidad_actual = max(0.4, velocidad_actual - 0.1)

    if centro < (centro_ideal - margen): # Izquierda
        aplicar_motores(velocidad_actual * 0.3, velocidad_actual, "rev", "fwd")
    elif centro > (centro_ideal + margen): # Derecha
        aplicar_motores(velocidad_actual, velocidad_actual * 0.3, "fwd", "rev")
    else: # Recto
        aplicar_motores(velocidad_actual, velocidad_actual, "fwd", "fwd")
    
    return velocidad_actual

buf = bytearray(2 * cam.width * cam.height)
threshold = 60
p_brain = Perceptron(input_size=2)
vel = 0.5
iteracion = 0



while True:
    cam.capture(buf)
    centro = detectar_centro_linea(buf, cam.width, cam.height, threshold)

    if centro is None:
        detener()
        print("Buscando línea...")
    else:
        debe_entrenar = (iteracion % 5 == 0)
        vel = ajustar_direccion(centro, cam.width, p_brain, vel, entrenar=debe_entrenar)
        print(f"Centro: {centro} | Vel IA: {vel:.2f} | Pesos: {[round(w,2) for w in p_brain.weights]}")

    iteracion += 1
    time.sleep(0.01)
