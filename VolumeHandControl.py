# کتابخانه‌های مورد نیاز
import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# تنظیمات دوربین
wCam, hCam = 640, 480  # ابعاد تصویر
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0  # برای محاسبه FPS

# ایجاد شیء تشخیص دست
detector = htm.handDetector(detectionCon=0.8, trackCon=0.8)

# تنظیمات کنترل صدا
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]
volStep = 3  # گام تغییر ولوم (3 واحد)
volPer = 50  # درصد ولوم اولیه (برای شروع از وسط)
isMuted = False  # وضعیت میوت
lastVol = 0  # ذخیره ولوم قبل از میوت
volBar = 275  # موقعیت اولیه نوار ولوم (متناظر با 50%)
lastActionTime = 0  # برای جلوگیری از تغییرات سریع

# حلقه اصلی
while True:
    success, img = cap.read()
    if not success:
        print("خطا در دسترسی به دوربین!")
        break

    # تشخیص دست
    img = detector.findHands(img, draw=True)  # رسم خطوط دست
    lmList, bbox = detector.findPosition(img, draw=False)  # بدون رسم نقاط

    # نمایش FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)

    # اگر دست تشخیص داده شد
    if len(lmList) >= 21 and bbox and (bbox[2] - bbox[0]) > 100:  # بررسی اندازه دست
        currentTime = time.time()

        # مختصات انگشتان
        thumb_x, thumb_y = lmList[4][1], lmList[4][2]  # شست (نقطه 4)
        index_x, index_y = lmList[8][1], lmList[8][2]  # اشاره (نقطه 8)
        middle_x, middle_y = lmList[12][1], lmList[12][2]  # وسط (نقطه 12)
        pinky_x, pinky_y = lmList[20][1], lmList[20][2]  # کوچک (نقطه 20)

        # محاسبه فاصله‌ها
        pinky_distance = math.hypot(pinky_x - thumb_x, pinky_y - thumb_y)
        index_distance = math.hypot(index_x - thumb_x, index_y - thumb_y)
        middle_distance = math.hypot(middle_x - thumb_x, middle_y - thumb_y)

        # آستانه برای تشخیص "چسبیدن" انگشت به شست
        threshold = 30  # فاصله کمتر از 30 پیکسل

        # ژست میوت/آن‌میوت: انگشت کوچک به شست
        if pinky_distance < threshold and currentTime - lastActionTime > 0.5:
            if not isMuted:
                lastVol = volume.GetMasterVolumeLevel()
                volume.SetMute(1, None)
                isMuted = True
            else:
                volume.SetMute(0, None)
                volume.SetMasterVolumeLevel(lastVol, None)
                isMuted = False
            lastActionTime = currentTime
            # نمایش وضعیت میوت
            status = "Muted" if isMuted else "Unmuted"
            color = (0, 0, 255) if isMuted else (0, 255, 0)
            cv2.putText(img, status, (150, 80), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)

        # ژست افزایش ولوم: انگشت اشاره به شست
        elif index_distance < threshold and currentTime - lastActionTime > 0.5 and not isMuted:
            volPer = min(volPer + volStep, 100)  # افزایش 3 واحدی
            vol = np.interp(volPer, [0, 100], [minVol, maxVol])
            volBar = np.interp(volPer, [0, 100], [400, 150])
            try:
                volume.SetMasterVolumeLevel(vol, None)
            except Exception as e:
                print(f"خطا در تنظیم ولوم: {e}")
            lastActionTime = currentTime
            cv2.putText(img, "Volume Up", (150, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (1, 255, 255), 2)

        # ژست کاهش ولوم: انگشت وسط به شست
        elif middle_distance < threshold and currentTime - lastActionTime > 0.5 and not isMuted:
            volPer = max(volPer - volStep, 0)  # کاهش 3 واحدی
            vol = np.interp(volPer, [0, 100], [minVol, maxVol])
            volBar = np.interp(volPer, [0, 100], [400, 150])
            try:
                volume.SetMasterVolumeLevel(vol, None)
            except Exception as e:
                print(f"خطا در تنظیم ولوم: {e}")
            lastActionTime = currentTime
            cv2.putText(img, "Volume Down", (150, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 1), 2)

        # رسم نقاط و خط برای ژست‌های فعال
        if pinky_distance < threshold:
            cv2.circle(img, (thumb_x, thumb_y), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (pinky_x, pinky_y), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (thumb_x, thumb_y), (pinky_x, pinky_y), (255, 0, 255), 3)
        elif index_distance < threshold:
            cv2.circle(img, (thumb_x, thumb_y), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (index_x, index_y), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 3)
        elif middle_distance < threshold:
            cv2.circle(img, (thumb_x, thumb_y), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (middle_x, middle_y), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (thumb_x, thumb_y), (middle_x, middle_y), (255, 0, 255), 3)

    # نمایش نوار ولوم
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)  # قاب
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)  # پر شده
    cv2.putText(img, f'Vol: {int(volPer)}%', (40, 430), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)

    # نمایش تصویر
    cv2.imshow("Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# آزادسازی منابع
cap.release()
cv2.destroyAllWindows()