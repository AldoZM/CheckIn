from mfrc522 import SimpleMFRC522
import requests
import time

reader = SimpleMFRC522()

# Cambia esto a la IP o hostname donde corre tu servidor Flask
SERVIDOR = "http://localhost:5000/checkin_rfid"

try:
    print("Acerque un tag RFID para hacer Check In...")
    while True:
        uid, _ = reader.read()
        uid_str = str(uid)
        print(f"🎯 UID detectado: {uid_str}")

        try:
            response = requests.post(SERVIDOR, data={"uid": uid_str})
            print(f"✅ Servidor respondió: {response.text}")
        except Exception as e:
            print(f"❌ Error al enviar al servidor: {e}")

        print("Esperando nuevo tag...\n")
        time.sleep(2)

except KeyboardInterrupt:
    print("Programa detenido por el usuario.")
finally:
    reader.cleanup()
