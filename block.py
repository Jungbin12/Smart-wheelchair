import cv2
import time
import threading
import RPi.GPIO as GPIO
from ultralytics import YOLO

# === YOLO 모델 로드 ===
model = YOLO("best2.onnx")
CLASS_NAMES = ["점자블럭", "선형블럭"]

# === 전역 변수 ===
frame = None
last_annotated_frame = None
running = True
inference_interval_sec = 1.0
last_inference_time = 0
current_state = "NONE"  # STOP, GO_FORWARD, NONE
distance1 = 999.0
distance2 = 999.0
brake_engaged = False

# === 핀 설정 ===
TRIG1 = 12
ECHO1 = 16
TRIG2 = 17
ECHO2 = 27
BUZZER = 18
SERVO_PIN = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.output(TRIG1, False)
GPIO.output(TRIG2, False)

# === 서보모터 PWM 설정 ===
servo_pwm = GPIO.PWM(SERVO_PIN, 50)
servo_pwm.start(0)

# === 거리 측정 함수 ===
def get_distance(trig_pin, echo_pin):
    GPIO.output(trig_pin, False)
    time.sleep(0.05)
    GPIO.output(trig_pin, True)
    time.sleep(0.00001)
    GPIO.output(trig_pin, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.04
    while GPIO.input(echo_pin) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return 999.0

    while GPIO.input(echo_pin) == 1:
        pulse_end = time.time()
        if pulse_end - pulse_start > 0.04:
            return 999.0

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

# === 부저 함수 ===
def beep(frequency=1000, duration=0.1):
    pwm = GPIO.PWM(BUZZER, frequency)
    pwm.start(50)
    time.sleep(duration)
    pwm.stop()

# === 서보 각도 설정 함수 ===
def set_servo_angle(angle):
    duty = 2 + (angle / 18)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.3)
    servo_pwm.ChangeDutyCycle(0)

# === 카메라 쓰레드 ===
def capture_thread():
    global frame, running
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    while running:
        ret, f = cap.read()
        if ret:
            frame = f.copy()
        else:
            print("❌ Failed to capture frame")
            break
    cap.release()

# === 초음파 거리 쓰레드 ===
def distance_thread():
    global distance1, distance2, running
    while running:
        try:
            distance1 = get_distance(TRIG1, ECHO1)
            distance2 = get_distance(TRIG2, ECHO2)
        except:
            distance1 = 999.0
            distance2 = 999.0
        time.sleep(0.1)

# === 부저 쓰레드 ===
def buzzer_thread():
    global current_state, running
    while running:
        try:
            if current_state == "STOP":
                beep(1000, 0.1)
                time.sleep(0.1)
            elif current_state == "GO_FORWARD":
                beep(700, 0.05)
                time.sleep(2)
            else:
                min_dist = min(distance1, distance2)
                if min_dist < 30:
                    beep(900, 0.1)
                    time.sleep(0.1)
                elif min_dist < 70:
                    beep(900, 0.1)
                    time.sleep(0.5)
                elif min_dist < 100:
                    beep(900, 0.1)
                    time.sleep(1.0)
                else:
                    time.sleep(0.2)
        except:
            time.sleep(0.2)

# === 쓰레드 실행 ===
threading.Thread(target=capture_thread, daemon=True).start()
threading.Thread(target=distance_thread, daemon=True).start()
threading.Thread(target=buzzer_thread, daemon=True).start()

# === 메인 루프 ===
try:
    print("🚘 시스템 시작 (Ctrl+C로 종료)")
    while True:
        if frame is None:
            continue

        now = time.time()
        if now - last_inference_time >= inference_interval_sec:
            last_inference_time = now
            input_frame = cv2.resize(frame, (640, 480))
            try:
                results = model(input_frame, verbose=False)
                last_annotated_frame = results[0].plot()
                boxes = results[0].boxes
                detected_classes = []

                for cls_id, conf in zip(boxes.cls.tolist(), boxes.conf.tolist()):
                    if conf >= 0.5:
                        class_name = CLASS_NAMES[int(cls_id)]
                        detected_classes.append(class_name)

                if "선형블럭" in detected_classes:
                    current_state = "STOP"
                elif "점자블럭" in detected_classes:
                    current_state = "GO_FORWARD"
                else:
                    current_state = "NONE"

                # ✅ 최소 거리 기준으로 브레이크 작동
                min_dist = min(distance1, distance2)
                if min_dist < 30 and not brake_engaged:
                    print("🛑 긴급 제동! (서보 90도)")
                    set_servo_angle(90)
                    brake_engaged = True
                elif min_dist >= 30 and brake_engaged:
                    print("✅ 브레이크 해제 (서보 0도)")
                    set_servo_angle(0)
                    brake_engaged = False

                brake_status = "긴급제동" if brake_engaged else "NONE"
                print(f"YOLO 추론 시간: {time.time() - now:.2f}초 | 상태: {current_state} | 거리1: {distance1}cm, 거리2: {distance2}cm | 브레이크: {brake_status}")

            except Exception as e:
                print("❌ YOLO 추론 오류:", e)
                current_state = "NONE"

        display_frame = last_annotated_frame if last_annotated_frame is not None else frame
        cv2.imshow("YOLO Real-Time View", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

finally:
    print("🛑 프로그램 종료")
    cv2.destroyAllWindows()
    servo_pwm.stop()
    GPIO.cleanup()