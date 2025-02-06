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
    OV7670_TEST_PATTERN_COLOR_BAR_FADE,
)
import random

# Configuración de la cámara
cam = CAM(
    d0_d7pinslist=[
        board.GP4,  # D0
        board.GP5,  # D1
        board.GP6,  # D2
        board.GP7,  # D3
        board.GP8,  # D4
        board.GP9,  # D5
        board.GP10,  # D6
        board.GP11,  # D7
    ],
    plk=board.GP12,     # Pixel clock
    xlk=board.GP13,     # External clock
    sda=board.GP14,     # I2C SDA
    scl=board.GP15,     # I2C SCL
    hs=board.GP16,      # Horizontal sync
    vs=board.GP17,      # Vertical sync
    ret=board.GP18,     # Reset
    pwdn=board.GP19     # Power down
)

# Configuración de los motores
motor_a_adelante = digitalio.DigitalInOut(board.GP20)  # IN1
motor_a_atras = digitalio.DigitalInOut(board.GP21)     # IN2
motor_b_adelante = digitalio.DigitalInOut(board.GP22)  # IN3
motor_b_atras = digitalio.DigitalInOut(board.GP26)     # IN4
enable_a = pwmio.PWMOut(board.GP27, frequency=1000, duty_cycle=32767)  # ENA
enable_b = pwmio.PWMOut(board.GP0, frequency=1000, duty_cycle=32767)  # ENB

motor_a_adelante.direction = digitalio.Direction.OUTPUT
motor_a_atras.direction = digitalio.Direction.OUTPUT
motor_b_adelante.direction = digitalio.Direction.OUTPUT
motor_b_atras.direction = digitalio.Direction.OUTPUT

cam.size = OV7670_SIZE_DIV16
cam.colorspace = OV7670_COLOR_YUV
cam.flip_y = True

def adelante(velocidad=1.0):
    motor_a_adelante.value = True
    motor_a_atras.value = False
    motor_b_adelante.value = True
    motor_b_atras.value = False
    enable_a.duty_cycle = int(65535 * velocidad)
    enable_b.duty_cycle = int(65535 * velocidad)

def atras(velocidad=1.0):
    motor_a_adelante.value = False
    motor_a_atras.value = True
    motor_b_adelante.value = False
    motor_b_atras.value = True
    enable_a.duty_cycle = int(65535 * velocidad)
    enable_b.duty_cycle = int(65535 * velocidad)

def detener():
    motor_a_adelante.value = False
    motor_a_atras.value = False
    motor_b_adelante.value = False
    motor_b_atras.value = False
    enable_a.duty_cycle = 0
    enable_b.duty_cycle = 0

def detectar_centro_linea(buf, width, height, threshold):
    filas_a_analizar = [height - 15,height - 1]  # Tres filas
    centros = []
    for fila_a_analizar in filas_a_analizar:
        inicio_fila = 2 * width * fila_a_analizar
        fin_fila = inicio_fila + 2 * width
        fila = bytearray(buf[i] for i in range(inicio_fila, fin_fila, 2))

        suma_posiciones = 0
        conteo_negro = 0
        for x, y_value in enumerate(fila):
            if y_value < threshold:
                suma_posiciones += x
                conteo_negro += 1

        if conteo_negro > 0:
            centros.append(suma_posiciones // conteo_negro)

    if centros:
        return sum(centros) // len(centros)  # Promedio de los centros
    return None

class Perceptron:
    def _init_(self, input_size, learning_rate=0.01):
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

def ajustar_direccion(centro, width, perceptron, velocidad, entrenar=False):
    margen_centro = width // 5
    if centro is None:
        print("Línea no detectada. Deteniendo.")
        detener()
        return velocidad, False  # Suspender el aprendizaje
    elif centro < (width // 2 - margen_centro):
        print("Línea a la izquierda. Girando a la izquierda.")
        motor_a_adelante.value = True
        motor_a_atras.value = False
        motor_b_adelante.value = False
        motor_b_atras.value = True
    elif centro > (width // 2 + margen_centro):
        print("Línea a la derecha. Girando a la derecha.")
        motor_a_adelante.value = False
        motor_a_atras.value = True
        motor_b_adelante.value = True
        motor_b_atras.value = False
    else:
        print("Línea centrada. Avanzando.")
        adelante(velocidad=velocidad)
        if entrenar:
            # Entrenar el perceptrón solo cuando está centrado
            inputs = [centro / width, velocidad]
            perceptron.train(inputs, target=1)  # Target = 1 (comportamiento correcto)

    # Ajustar la velocidad en función de las predicciones
    inputs = [centro / width, velocidad]
    if perceptron.predict(inputs) == 1:  # Si predice correctamente
        velocidad = min(1.0, velocidad + 0.01)
    else:
        velocidad = max(0.5, velocidad - 0.05)

    return velocidad, True  # Continuar el aprendizaje

buf = bytearray(2 * cam.width * cam.height)
threshold = 60
perceptron = Perceptron(input_size=2, learning_rate=0.01)  # Tasa de aprendizaje reducida
velocidad = 0.5
contador_entrenamiento = 0  # Contador para controlar la frecuencia de entrenamiento
detectando_linea = True  # Estado inicial: detectando la línea

while True:
    cam.capture(buf)
    centro = detectar_centro_linea(buf, cam.width, cam.height, threshold)

    if centro is None:
        # Si no se detecta la línea, detener y suspender el aprendizaje
        velocidad = 0.5
        detectando_linea = False
        detener()
    else:
        # Si se detecta la línea, reanudar el aprendizaje
        detectando_linea = True

    if detectando_linea:
        # Entrenar el perceptrón solo cada 10 iteraciones y cuando está centrado
        entrenar = (contador_entrenamiento % 10 == 0) and (centro is not None and (cam.width // 2 - cam.width // 5) <= centro <= (cam.width // 2 + cam.width // 5))
        velocidad, _ = ajustar_direccion(centro, cam.width, perceptron, velocidad, entrenar=entrenar)
    else:
        # Si no se detecta la línea, no entrenar
        print("Línea no detectada. Aprendizaje suspendido.")

    contador_entrenamiento += 1
    time.sleep(0.1)
