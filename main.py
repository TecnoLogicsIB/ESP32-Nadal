import esp32
from machine import Pin, TouchPad, deepsleep, SoftI2C
import random
import neopixel
import utime
import pca9685

Tbreak = TouchPad(Pin(15))  
Tsleep = TouchPad(Pin(32))  
Twake = TouchPad(Pin(33))
estrella = Pin(27, Pin.OUT)
arbre1 = Pin(2, Pin.OUT)
arbre2 = Pin(0, Pin.OUT)
arbre3 = Pin(4, Pin.OUT)
arbre4 = Pin(16, Pin.OUT)
arbre5 = Pin(17, Pin.OUT)
arbres = [arbre1, arbre2, arbre3, arbre4, arbre5]

n=30
n1=16
np1 = neopixel.NeoPixel(Pin(13), n)  # estrella
np2 = neopixel.NeoPixel(Pin(12), n)
np3 = neopixel.NeoPixel(Pin(14), n)
np4 = neopixel.NeoPixel(Pin(26), n)  # nucli estrella

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000) # configuració I2C
pca = pca9685.PCA9685(i2c)  # Inicializació del PCA9685
pca.freq(50)  # 50 és la frecuencia PWM típica para servos
channels = [12, 13, 14, 15] # Canales donde están conectados los 4 servos (canales 12 a 15)

temps_estrella = 0  # cua estrella
temps_pesebre = 0
temps_electric = 0
temps_riu = 0
temps_nucli = 0  # estrella
temps_funcionament = 0

estat = False  # estrella
base_colores = [
    (255, 0, 0),     # Rojo
    (255, 127, 0),   # Naranja
    (255, 255, 0),   # Amarillo
    (0, 255, 0),     # Verde
    (0, 0, 255),     # Azul
    (75, 0, 130),    # Índigo
    (238, 130, 238)  # Violeta
]  # pesebre
led_pos = 0  # electric

def destellos():    # comportament de l'estrella: encesa intermitent
    global estat
    estat = not estat
    estrella.value(estat)
    
def pesebre(r,g,b):
    for i in range(n):
        np1[i] = (r, g, b)
    np1.write()

def generar_arcoiris(num_colores):  # colors pesebre
    colores = []    
    pasos_por_color = num_colores // len(base_colores)  
    colores_restantes = num_colores % len(base_colores)  
    for i in range(len(base_colores)):
        color_inicial = base_colores[i]
        color_final = base_colores[(i + 1) % len(base_colores)]
        pasos = pasos_por_color + (1 if i < colores_restantes else 0)       
        for j in range(pasos):
            t = j / pasos
            r = int(color_inicial[0] + (color_final[0] - color_inicial[0]) * t)
            g = int(color_inicial[1] + (color_final[1] - color_inicial[1]) * t)
            b = int(color_inicial[2] + (color_final[2] - color_inicial[2]) * t)
            colores.append((r, g, b))
    return colores[:num_colores]  

colores_arcoiris = generar_arcoiris(n)  # generamos la lista de colores para los 30 LEDs

def actualizar_arcoiris():  # actualiza la tira de LEDs con el arcoíris del pesebre
    global colores_arcoiris
    colores_arcoiris.append(colores_arcoiris.pop(0))  
    for i in range(n):
        np1[i] = colores_arcoiris[i]
    np1.write()
    
def mover_led():  #electric
    global led_pos
    for j in range(n):
        np2[j] = (0, 0, 0)  # Apaga el LED en la posición j
    np2[led_pos] = (255, 255, 255)  # Blanco es (255, 255, 255)
    np2.write()
    led_pos += 1 # Avanza la posición del LED
    if led_pos >= n: # Si hemos llegado al final de la tira, reinicia la posición
        led_pos = 0

def agua():  # riu
    for i in range(n): # Apaga todos los LEDs
        np3[i] = (0, 0, 20)  # para que no se apaguen del todo, 20 de azul
    np3.write()
    # Selecciona LEDs al azar para encender, simulando el movimiento
    for i in range(random.randint(5, 10)):  # Número aleatorio de LEDs que se activan
        led_index = random.randint(0, n - 1)
        # Genera un color azul o verde para simular agua
        color = (random.randint(0, 50), random.randint(0, 50), random.randint(150, 255))  # Azul
        np3[led_index] = color
    np3.write()

def change_brightness():  # nucli estrella
    # Mantener el color amarillo (255, 255, 0)
    base_color = (255, 155, 0)  # Color amarillo
    
    # Generar un valor aleatorio de brillo entre 0 y 255
    brightness = random.randint(0, 255)
    
    # Ajustar el color con el nivel de brillo aleatorio
    color = (int(base_color[0] * brightness / 255), 
             int(base_color[1] * brightness / 255), 
             int(base_color[2] * brightness / 255))
    
    # Aplicar el color ajustado a todos los LEDs
    for i in range(n1):
        np4[i] = color  # Asignar el color con el brillo ajustado
    np4.write()  # Enviar los colores a los Neopixels

def clear():  # apaga totes les tires de leds
    for i in range(n):
        np1[i] = (0, 0, 0)
        np2[i] = (0, 0, 0)
        np3[i] = (0, 0, 0)
        np4[i] = (0, 0, 0)
    np1.write()
    np2.write()
    np3.write()
    np4.write()
    
def rotate_servos():  # aerogeneradors
    for channel in channels:
        pca.duty(channel, 290)  # PWM bajo (70) para giro horario (1000 a 1100 - 1500)
def para_servos():
    for channel in channels:
        pca.duty(channel, 300)  # PWM 300 detiene el servo

def encen_arbres():
    for i in range (0,5):
        arbres[i].on()
def apaga_arbres():
    for i in range (0,5):
        arbres[i].off()

# configura el despertar de deepsleep en tocar el sensor tàctil:
Twake.config(250)  # 250: lectura per considerar tocat el sensor
esp32.wake_on_touch(True)  

print('---- HOLA ----')  # per comprovar el despertar de deepsleep
rotate_servos()
encen_arbres()

while True:
    temps_actual = utime.ticks_ms()

    if utime.ticks_diff(temps_actual, temps_estrella) >= random.randint(10,1000):
        destellos()
        temps_estrella = temps_actual
    
    #if utime.ticks_diff(temps_actual, temps_pesebre) >= random.randint(100,1000):
        #pesebre(random.randint(0,255),random.randint(0,255),0)
        #temps_pesebre = temps_actual
    
    if utime.ticks_diff(temps_actual, temps_pesebre) >= random.randint(100,500):
        actualizar_arcoiris()
        temps_pesebre = temps_actual
    
    if utime.ticks_diff(temps_actual, temps_electric) >= 100:
        mover_led()
        temps_electric = temps_actual
        
    if utime.ticks_diff(temps_actual, temps_riu) >= random.randint(100,300):
        agua()
        temps_riu = temps_actual
    
    if utime.ticks_diff(temps_actual, temps_nucli) >= random.randint(100,500):
        change_brightness()
        temps_nucli = temps_actual
    
    if utime.ticks_diff(temps_actual, temps_funcionament) >= 900000:  # 15 minuts de funcionament: 900000 ms
        print('---- VAIG A DORMIR ----')
        deepsleep()
        temps_funcionament = temps_actual    
    
# ---------------------------------------------------------------------------------------------
    
    if (Tsleep.read()<250):    #activació de deepsleep
        clear()
        para_servos()
        apaga_arbres()
        print('---- VAIG A DORMIR ----')
        deepsleep()

    elif (Tbreak.read()<250):  # cancela l'execució (break)
        estrella.value(0)
        clear()
        para_servos()
        apaga_arbres()
        print('---- ADEU ----')
        break

    utime.sleep(.01)  # petita pausa per no saturar el bucle
