
import network
import socket
from machine import Pin, PWM, I2C
import time
import ssd1306

# Configuración de los pines del motor
in1_left = Pin(8, Pin.OUT)
in2_left = Pin(9, Pin.OUT)
en_left = PWM(Pin(6))
en_left.freq(1000)

in1_right = Pin(4, Pin.OUT)
in2_right = Pin(5, Pin.OUT)
en_right = PWM(Pin(7))
en_right.freq(1000)

# Configuración de la pantalla OLED
i2c = I2C(0, scl=Pin(17), sda=Pin(16))  # Ajusta los pines si es necesario
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

# Función para actualizar la pantalla OLED
def mostrar_en_pantalla(comando, ip=None):
    oled.fill(0)  # Limpiar pantalla
    oled.text(comando, 0, 0)  # Mostrar comando
    if ip:
        oled.text(ip, 0, 10)  # Mostrar IP en la segunda línea
    oled.show()

# Funciones de control de los motores
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

# Conectando a la red WiFi
ssid = 'perrito32'
password = '12345678'
wlan = network.WLAN(network.STA_IF)

def conectar_wifi():
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        pass
    
    ip = wlan.ifconfig()[0]
    print('Conexión establecida, IP:', ip)
    mostrar_en_pantalla(f'IP: {ip}', ip)  # Mostrar IP en la pantalla OLED

conectar_wifi()

# Configuración del servidor
address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(address)
s.listen(1)
print('Servidor escuchando en', address)

# Bucle principal del servidor
while True:
    cl, addr = s.accept()
    print('Conexión desde', addr)
    request = cl.recv(1024)
    request = str(request)

    print("Solicitud recibida:", request)

    # Manejamos las solicitudes
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
    
    # Respuesta HTTP
    response = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Animación 3D - Botones en la cara 5 del cubo</title>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }
        #canvas-container {
            width: 100%;
            height: 100vh;
            position: absolute;
            top: 0;
            left: 0;
        }
    </style>
</head>
<body>
    <div id="canvas-container"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        // Crear la escena
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('canvas-container').appendChild(renderer.domElement);

        // Crear un canvas para todos los botones en una cara del cubo
        const createButtonsTexture = () => {
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 256;
            const context = canvas.getContext('2d');

            // Fondo del canvas
            context.fillStyle = '#222';
            context.fillRect(0, 0, canvas.width, canvas.height);

            // Estilo para los botones
            context.fillStyle = '#28a745';
            context.font = '20px Arial';
            context.textAlign = 'center';
            context.fillStyle = '#fff';

            // Dibujar el botón "Adelante"
            context.fillStyle = '#a22020';
            context.fillRect(85, 40, 90, 30);
            context.fillStyle = '#fff';
            context.fillText('Avanzar', 130, 60);

            // Dibujar el botón "Atrás"
            context.fillStyle = '#a22020';
            context.fillRect(90, 160, 80, 30);
            context.fillStyle = '#fff';
            context.fillText('Atrás', 130, 180);

            // Dibujar el botón "Izquierda"
            context.fillStyle = '#a22020';
            context.fillRect(35, 100, 90, 30);
            context.fillStyle = '#fff';
            context.fillText('Izquierda', 80, 120);

            // Dibujar el botón "Derecha"
            context.fillStyle = '#a22020';
            context.fillRect(135, 100, 90, 30);
            context.fillStyle = '#fff';
            context.fillText('Derecha', 180, 120);
            
            // Dibujar el botón "Detenerse"
            context.fillStyle = '#ffffff';
            context.fillRect(80, 210, 100, 32);
            context.fillStyle = '#000';
            context.fillText('Detenerse', 130, 233);

            return new THREE.CanvasTexture(canvas);
        };

        // Crear materiales para las caras del cubo
        const materials = [
            new THREE.MeshBasicMaterial({ color: 0x9d0909 }), // Cara 1
            new THREE.MeshBasicMaterial({ color: 0x9d0909 }), // Cara 2
            new THREE.MeshBasicMaterial({ color: 0x9d0909 }), // Cara 3
            new THREE.MeshBasicMaterial({ color: 0x9d0909 }), // Cara 4
            new THREE.MeshBasicMaterial({ map: createButtonsTexture() }), // Cara 5 (Superior)
            new THREE.MeshBasicMaterial({ color: 0xa22020 })  // Cara 6
        ];

        // Crear el cubo con geometría aplanada
        const geometry = new THREE.BoxGeometry(5, 5, 0.2);
        const flattenedCube = new THREE.Mesh(geometry, materials);
        scene.add(flattenedCube);

        // Posicionar la cámara
        camera.position.z = 4;
        camera.position.x = 0;
        camera.position.y = 0;

        // Variables de control para rotar el cubo
        let rotateX = 0.0;
        let rotateY = 0.01;

        // Animar la escena
        function animate() {
            requestAnimationFrame(animate);

            // Rotar el cubo
            flattenedCube.rotation.x = rotateX;
            flattenedCube.rotation.y += rotateY;

            // Renderizar la escena
            renderer.render(scene, camera);
        }
        animate();

        // Ajustar el renderizado cuando la ventana cambia de tamaño
        window.addEventListener('resize', () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            renderer.setSize(width, height);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
        });

        // Detectar clics en las texturas del cubo
        window.addEventListener('click', (event) => {
            const mouse = new THREE.Vector2(
                (event.clientX / window.innerWidth) * 2 - 1,
                -(event.clientY / window.innerHeight) * 2 + 1
            );
            const raycaster = new THREE.Raycaster();
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObject(flattenedCube);

            if (intersects.length > 0) {
                const uv = intersects[0].uv;  // Coordenadas UV del punto clicado
                const faceIndex = intersects[0].face.materialIndex;

                if (faceIndex === 4) {  // La cara 5 con los botones
                    // Coordenadas UV mapeadas en el canvas (entre 0 y 1)
                    const u = uv.x;
                    const v = uv.y;

                    if (u > 0.35 && u < 0.65 && v > 0.7 && v < 0.8) {
                        window.location.href = '/avanzar'; // Redireccionar a la ruta de avanzar
                    } else if (u > 0.35 && u < 0.65 && v > 0.3 && v < 0.4) {
                        window.location.href = '/atras'; // Redireccionar a la ruta de atrás
                    } else if (u > 0.15 && u < 0.35 && v > 0.5 && v < 0.6) {
                        window.location.href = '/izquierda'; // Redireccionar a la ruta de izquierda
                    } else if (u > 0.65 && u < 0.85 && v > 0.5 && v < 0.6) {
                        window.location.href = '/derecha'; // Redireccionar a la ruta de derecha
                    } else if (u > 0.30 && u < 0.7 && v > 0.04 && v < 0.3) {
                        window.location.href = '/detenerse'; // Redireccionar a la ruta de detenerse
                    }
                }
            }
        });
    </script>
</body>
</html>"""



    cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
    cl.send(response)
    cl.close()

