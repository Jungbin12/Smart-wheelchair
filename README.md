# ♿ Smart Wheelchair for the Visually Impaired
<p>성결대학교 졸업프로젝트</p>
> **AI 실시간 점자 블록 인식 및 자동 긴급 제동 시스템**
> 본 프로젝트는 시각장애인이 휠체어 주행 중 겪는 안전 문제를 해결하기 위해 Deep Learning 기반의 노면 인식과 초음파 센서 기반의 자동 제동 기술을 결합한 스마트 보행 보조 장치입니다.
<img src="https://github.com/Jungbin12/Smart-wheelchair/blob/c0f9050b6aa123eba4e26c5816e83dda62cd67fb/%EC%A0%84%EC%B2%B4%20%EC%99%B8%EA%B4%80%20img%20(1).png" width="800" alt="휠체어 전체 사진">

---

## 1. 개요 및 배경
*  **수행 기간**: 2025.03 ~ 2025.06
*  **팀명**: 아이들
*  **핵심 기술**: Raspberry Pi 4, YOLO v8, OpenCV, Python, Servo Control, Firebase
*  **나의 역할**: Software Engineer
    * 라즈베리파이 메인 제어 시스템 설계 및 구현
    * YOLO v8 모델을 활용한 점자 블록(점형/선형) 실시간 객체 인식 최적화
    * 초음파 센서 데이터 처리를 통한 긴급 제동 및 부저 알림 로직 개발
    * 시스템 안정성을 위한 Multi-threading 구조 설계
<p align="center">
   <img src="https://github.com/Jungbin12/Smart-wheelchair/blob/40cf56e8d5787853cc9198fa572b70eefaa6b31a/%EA%B8%B0%EB%8A%A5%20%EB%B8%94%EB%A1%9D%EB%8F%84%20img%20(2).png" width="400" alt="점자블록 인식 화면">
</p>
---

## 2. 주요 기능 및 기술적 특징
* 🔍 **실시간 점자 블록 인식 (AI Inference)**
    * Model: YOLO v8 기반 커스텀 학습 모델 사용 (best2.onnx)
    * Detection: 카메라를 통해 노면의 **'점형 블록(정지)'**과 **'선형 블록(유도)'**을 실시간으로 구분합니다.
    * Processing: Raspberry Pi의 자원을 효율적으로 사용하기 위해 ONNX 포맷으로 변환하여 추론 속도를 최적화했습니다.

* 🛡️ **지능형 자동 제동 시스템 (Safety Control)**
    * Obstacle Detection: 2개의 초음파 센서를 사용하여 전방의 장애물을 실시간 모니터링합니다.
    * Active Braking: 장애물 거리가 30cm 이내로 좁혀질 경우, 서보모터를 90도로 회전시켜 휠체어 바퀴를 물리적으로 고정하는 긴급 제동을 실행합니다.
    * Adaptive Feedback: 거리에 따라 부저의 울림 간격을 조정(1.0s → 0.5s → 0.1s)하여 사용자에게 직관적인 위험 신호를 전달합니다.

* 📱 **긴급 호출 및 위치 공유 (IoT)**
    * 사고 발생 시 휠체어의 버튼을 누르면 GPS 좌표가 Firebase를 통해 보호자의 전용 앱으로 즉각 전송됩니다.

---

## 3. 시스템 아키텍처 (System Architecture)
* **Software Stack**
    * **Language**: Python 3.x
    * **Libraries**: OpenCV, Ultralytics, RPi.GPIO, Threading, Time
    * **Environment**: Raspberry Pi OS (64-bit)

* **Hardware Components**
    * **Main Board**: Raspberry Pi 4 Model B
    * **Vision**: Raspberry Pi Camera Module
    * **Distance**: HC-SR04 Ultrasonic Sensor (x2)
    * **Actuator**: MG996R High Torque Servo Motor (Brake)
    * **Alert**: Active Buzzer

<img src="https://github.com/Jungbin12/Smart-wheelchair/blob/40cf56e8d5787853cc9198fa572b70eefaa6b31a/%EA%B8%B0%EB%8A%A5%20%EC%9E%91%EB%8F%99%20img%20(3).png" width="700" alt="시스템 구성도">
---

## 4. 핵심 알고리즘 Flow
```Python
# 멀티쓰레딩 기반 제어 로직 예시
def safety_control_loop():
    while True:
        distance = get_ultrasonic_distance()
        
        # 1. 장애물 거리 기반 브레이크 제어
        if distance < 30:
            activate_servo_brake(90)  # 브레이크 작동
            buzzer_alert(interval=0.1) # 긴급 경고음
        else:
            activate_servo_brake(0)   # 브레이크 해제
            
        # 2. YOLO 인식 결과 기반 음성 안내
        if detected_class == "Point_Block":
            play_voice_guidance("정지 블록입니다.")
        elif detected_class == "Line_Block":
            play_voice_guidance("유도 블록입니다.")
```

---

## 5. 프로젝트 결과 및 성과
* **정확도**: 실외 환경에서 다양한 조도 조건 하에 점자 블록 인식률 90% 이상 달성
* **반응 속도**: 추론부터 제동까지의 지연 시간을 최소화하여 보행 속도 내 안전성 확보
* **확장성**: 저비용 임베디드 보드에서도 딥러닝 모델이 원활히 동작함을 검증하여 상용화 가능성 제시
