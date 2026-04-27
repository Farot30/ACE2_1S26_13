import json
import os
import time
from datetime import datetime, timezone

import cv2
import easyocr
from dotenv import load_dotenv
from ultralytics import YOLO

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None


load_dotenv()


# Configuracion minima
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.25"))
COOLDOWN_SECONDS = int(os.getenv("DETECTION_COOLDOWN_SECONDS", "3"))
MAX_FRAMES = int(os.getenv("MAX_FRAMES", "0"))
EASYOCR_LANGUAGES = [lang.strip() for lang in os.getenv("EASYOCR_LANGUAGES", "en").split(",") if lang.strip()]

MQTT_ENABLED = os.getenv("MQTT_ENABLED", "true").lower() == "true"
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC_VEHICLE", "park-guard/viv/vehicle/type")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "viv-detector")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

MONGO_ENABLED = os.getenv("MONGO_ENABLED", "false").lower() == "true"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "park_guard")
MONGO_COLLECTION = os.getenv("MONGO_PLATES_COLLECTION", "authorized_plates")


def create_mqtt_client():
    if not MQTT_ENABLED or mqtt is None:
        return None

    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
        return client
    except Exception as exc:
        print(f"MQTT no disponible, se continua sin publicar eventos: {exc}")
        return None


def create_mongo_collection():
    if not MONGO_ENABLED or MongoClient is None:
        return None
    mongo_client = MongoClient(MONGO_URI)
    return mongo_client[MONGO_DB][MONGO_COLLECTION]


def is_plate_authorized(collection, plate: str) -> bool:
    if collection is None:
        return False
    if not plate or plate == "UNKNOWN":
        return False
    return collection.find_one({"plate": plate.upper()}) is not None


def get_fee(vehicle_type: str) -> float:
    return 10.0 if vehicle_type == "car" else 5.0


def create_ocr_reader():
    try:
        return easyocr.Reader(EASYOCR_LANGUAGES, gpu=False)
    except Exception as exc:
        print(f"EasyOCR no disponible, se continua sin lectura de placa: {exc}")
        return None


def clean_plate_text(text: str) -> str:
    return "".join(character for character in text.upper() if character.isalnum())


def read_plate(reader, frame, box) -> tuple[str, float]:
    if reader is None or box is None:
        return "UNKNOWN", 0.0

    x1, y1, x2, y2 = box
    height = y2 - y1
    width = x2 - x1

    plate_y1 = max(0, y2 - max(30, (height * 45) // 100))
    plate_y2 = min(frame.shape[0], y2)
    plate_x1 = max(0, x1 + max(0, width // 10))
    plate_x2 = min(frame.shape[1], x2 - max(0, width // 10))

    plate_roi = frame[plate_y1:plate_y2, plate_x1:plate_x2]
    if plate_roi.size == 0:
        return "UNKNOWN", 0.0

    plate_roi = cv2.resize(plate_roi, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # Debug: guardar la región de placa para revisar
    try:
        cv2.imwrite("debug_plate_region.jpg", plate_roi)
    except Exception:
        pass

    results = reader.readtext(
        plate_roi,
        detail=1,
        paragraph=False,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    )
    if not results:
        return "UNKNOWN", 0.0

    best_text = "UNKNOWN"
    best_confidence = 0.0

    for _bbox, text, confidence in results:
        normalized_text = clean_plate_text(text)
        if normalized_text and confidence > best_confidence:
            best_text = normalized_text
            best_confidence = float(confidence)

    return best_text, best_confidence


def main() -> None:
    model = YOLO(YOLO_MODEL)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la camara con indice {CAMERA_INDEX}")

    ocr_reader = create_ocr_reader()
    mqtt_client = create_mqtt_client()
    plates_collection = create_mongo_collection()
    last_emit = 0.0
    last_event = None
    use_display = True
    processed_frames = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            best = None

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    label = model.names[int(box.cls[0])]

                    if label not in ["car", "motorcycle"] or confidence < YOLO_CONFIDENCE:
                        continue

                    if best is None or confidence > best["confidence"]:
                        best = {
                            "label": label,
                            "confidence": confidence,
                            "box": (x1, y1, x2, y2),
                        }

            if best:
                x1, y1, x2, y2 = best["box"]
                label = best["label"]
                confidence = best["confidence"]

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"{label} {confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                if (time.time() - last_emit) >= COOLDOWN_SECONDS:
                    plate_text, plate_confidence = read_plate(ocr_reader, frame, best["box"])
                    authorized = is_plate_authorized(plates_collection, plate_text)
                    event = {
                        "event_type": "viv_vehicle_detected",
                        "source": "viv",
                        "vehicle_type": label,
                        "confidence": confidence,
                        "plate_text": plate_text,
                        "plate_confidence": plate_confidence,
                        "plate_authorized": authorized,
                        "access_granted": authorized,
                        "fee_quetzales": get_fee(label),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    if mqtt_client is not None:
                        mqtt_client.publish(MQTT_TOPIC, json.dumps(event), qos=1)

                    print("Evento VIV:", event)
                    last_event = event
                    last_emit = time.time()

            if use_display:
                try:
                    cv2.imshow("VIV - Deteccion Vehicular", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        if last_event is not None:
                            print("JSON resultante al salir:")
                            print(json.dumps(last_event, indent=2, ensure_ascii=False))
                        else:
                            print("No se generó ningun JSON antes de salir.")
                        break
                except cv2.error:
                    use_display = False
                    print("Vista en pantalla no disponible, continuando en modo consola.")

            processed_frames += 1
            if MAX_FRAMES > 0 and processed_frames >= MAX_FRAMES:
                break
    finally:
        cap.release()
        if use_display:
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


if __name__ == "__main__":
    main()