
import network
import socket
from machine import Pin, PWM, I2C
import time
import ssd1306

in1_left = Pin(8, Pin.OUT)
in2_left = Pin(9, Pin.OUT)
en_left = PWM(Pin(6))
en_left.freq(1000)

in1_right = Pin(4, Pin.OUT)
in2_right = Pin(5, Pin.OUT)
en_right = PWM(Pin(7))
en_right.freq(1000)

i2c = I2C(0, scl=Pin(17), sda=Pin(16)) 
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

def mostrar_en_pantalla(comando, ip=None):
    oled.fill(0) 
    oled.text(comando, 0, 0) 
    if ip:
        oled.text(ip, 0, 10) 
    oled.show()

def control_left_motor(direction, speed):
    if direction == "forward":
        in1_left.value(1)
        in2_left.value(0)
    elif direction == "backward":
        in1_left.value(0)
        in2_left.value(1)
    en_left.duty_u16(int(speed * 65535))

def control_right_motor(direction, speed):
    if direction == "forward":
        in1_right.value(1)
        in2_right.value(0)
    elif direction == "backward":
        in1_right.value(0)
        in2_right.value(1)
    en_right.duty_u16(int(speed * 65535))

def stop_motors():
    control_left_motor("forward", 0)
    control_right_motor("forward", 0)

ssid = 'Carro'
password = '12345678'
wlan = network.WLAN(network.STA_IF)

def conectar_wifi():
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        pass
    
    ip = wlan.ifconfig()[0]
    print('Conexión establecida, IP:', ip)
    mostrar_en_pantalla(f'IP: {ip}', ip)

conectar_wifi()

address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(address)
s.listen(1)
print('Servidor escuchando en', address)

while True:
    cl, addr = s.accept()
    print('Conexión desde', addr)
    request = cl.recv(1024)
    request = str(request)

    print("Solicitud recibida:", request)

    if 'GET /avanzar' in request:
        control_left_motor("forward", 0.55)
        control_right_motor("forward", 0.6)
        mostrar_en_pantalla("AVANZANDO", wlan.ifconfig()[0])
    elif 'GET /retroceder' in request:
        control_left_motor("backward", 0.55)
        control_right_motor("backward", 0.6)
        mostrar_en_pantalla("RETROCEDIENDO", wlan.ifconfig()[0])
    elif 'GET /izquierda' in request:
        control_left_motor("backward", 0)
        control_right_motor("forward", 0.6)
        mostrar_en_pantalla("GIRANDO IZQUIERDA", wlan.ifconfig()[0])
    elif 'GET /derecha' in request:
        control_left_motor("forward", 0.6)
        control_right_motor("backward", 0)
        mostrar_en_pantalla("GIRANDO DERECHA", wlan.ifconfig()[0])
    elif 'GET /detener' in request:
        stop_motors()
        mostrar_en_pantalla("DETENIENDO", wlan.ifconfig()[0])
    
response = """<!DOCTYPE html>
<html>

<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robot Controller</title>

    <style>

        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            text-align: center;
            margin: 0;
        }

        h1 {
            margin-top: 20px;
        }

        .container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 70vh;
        }

        .grid {
            display: grid;
            grid-template-columns: 100px 100px 100px;
            grid-template-rows: 100px 100px 100px;
            gap: 15px;
        }

        button {
            font-size: 22px;
            border: none;
            border-radius: 15px;
            background: #e63946;
            color: white;
            cursor: pointer;
        }

        button:active {
            background: #ff6b6b;
        }

        .stop {
            background: white;
            color: black;
            font-weight: bold;
        }

    </style>
</head>

<body>

    <h1>Robot WiFi</h1>
    <p>Control del Carro</p>

    <div class="container">

        <div class="grid">

    <div></div>

    <button
        onmousedown="send('/avanzar')"
        onmouseup="send('/detener')"
        ontouchstart="send('/avanzar')"
        ontouchend="send('/detener')">
        &uarr;
    </button>

    <div></div>

    <button
        onmousedown="send('/izquierda')"
        onmouseup="send('/detener')"
        ontouchstart="send('/izquierda')"
        ontouchend="send('/detener')">
        &larr;
    </button>

    <button class="stop"
        onclick="send('/detener')">
        PARAR
    </button>

    <button
        onmousedown="send('/derecha')"
        onmouseup="send('/detener')"
        ontouchstart="send('/derecha')"
        ontouchend="send('/detener')">
        &rarr;
    </button>

    <div></div>

    <button
        onmousedown="send('/retroceder')"
        onmouseup="send('/detener')"
        ontouchstart="send('/retroceder')"
        ontouchend="send('/detener')">
        &darr;
    </button>

    <div></div>

</div>

    </div>

    <script>

        function send(cmd) {
            fetch(cmd)
        }

    </script>

</body>

</html>
"""

