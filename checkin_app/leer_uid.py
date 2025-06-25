from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    print("Acerca el tag al lector...")
    uid, text = reader.read()
    print("UID leído:", uid)
except Exception as e:
    print("❌ Error:", e)
finally:
    import RPi.GPIO as GPIO
    GPIO.cleanup()
