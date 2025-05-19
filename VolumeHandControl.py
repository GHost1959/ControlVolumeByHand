# کتابخانه‌های مورد نیاز
import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from collections import deque

# تنظیمات دوربین
wCam, hCam = 480, 360  # رزولوشن بهینه برای FPS بالا
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0  # برای محاسبه FPS

# ایجاد شیء تشخیص دست
detector = htm.handDetector(detectionCon=0.7, trackCon=0.7, maxHands=1)  # بهینه برای یک دست

# تنظیمات کنترل صدا
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volStep = 3  # گام تغییر ولوم
volPer = 0  # درصد ولوم
isMuted = False  # وضعیت میوت
lastVol = 0  # ذخیره ولوم قبل از میوت
volBar = 400  # موقعیت نوار ولوم
lastActionTime = 0  # برای تأخیر اکشن‌ها
volHistory = deque(maxlen=3)  # میانگین‌گیری با 3 مقدار

# تابع برای همگام‌سازی ولوم با سیستم
def sync_volume():
    global volPer, volBar
    try:
        current_vol = volume.GetMasterVolumeLevelScalar()
        volPer = current_vol * 100  # تبدیل به درصد
        volPer = round(volPer / volStep) * volStep  # پله‌ای کردن
        volPer = max(0, min(100, volPer))  # محدود به 0-100
        volBar = np.interp(volPer, [0, 100], [400, 150])
        return volPer
    except Exception as e:
        print(f"خطا در خواندن ولوم سیستم: {e}")
        return volPer

# تابع برای پیش‌پردازش تصویر (بهبود نور)
def preprocess_image(img):
    img = cv2.convertScaleAbs(img, alpha=1.1, beta=10)  # افزایش روشنایی و کنتراست
    return img

# مقداردهی اولیه ولوم
volPer = sync_volume()

# حلقه اصلی
while True:
    success, img = cap.read()
    if not success:
        print("خطا در دسترسی به دوربین!")
        break

    # پیش‌پردازش تصویر
    img = preprocess_image(img)

    # تشخیص دست
    img = detector.findHands(img, draw=True)
    lmList, bbox = detector.findPosition(img, draw=False)

    # نمایش FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 0), 2)

    # اگر دست تشخیص داده شد
    if len(lmList) >= 21 and bbox and (bbox[2] - bbox[0]) > 80:  # کاهش آستانه اندازه دست
        currentTime = time.time()

        # مختصات انگشتان
        thumb_x, thumb_y = lmList[4][1], lmList[4][2]  # شست
        index_x, index_y = lmList[8][1], lmList[8][2]  # اشاره
        middle_x, middle_y = lmList[12][1], lmList[12][2]  # وسط
        pinky_x, pinky_y = lmList[20][1], lmList[20][2]  # کوچک
        wrist_x, wrist_y = lmList[0][1], lmList[0][2]  # مچ

        # محاسبه اندازه دست (برای نرمال‌سازی)
        hand_size = math.hypot(index_x - wrist_x, index_y - wrist_y)
        scale_factor = hand_size / 100  # مقیاس‌بندی نسبت به اندازه دست
        threshold = max(20, min(50, 30 / scale_factor))  # آستانه پویا

        # محاسبه فاصله‌ها
        pinky_distance = math.hypot(pinky_x - thumb_x, pinky_y - thumb_y)
        index_distance = math.hypot(index_x - thumb_x, index_y - thumb_y)
        middle_distance = math.hypot(middle_x - thumb_x, middle_y - thumb_y)

        # ژست میوت/آن‌میوت: انگشت کوچک به شست
        if pinky_distance < threshold and currentTime - lastActionTime > 0.5:
            if not isMuted:
                lastVol = volume.GetMasterVolumeLevelScalar()
                volume.SetMute(1, None)
                isMuted = True
            else:
                volume.SetMute(0, None)
                volume.SetMasterVolumeLevelScalar(lastVol, None)
                isMuted = False
                volPer = sync_volume()
            lastActionTime = currentTime
            status = "Muted" if isMuted else "Unmuted"
            color = (0, 0, 255) if isMuted else (0, 255, 0)
            cv2.putText(img, status, (120, 60), cv2.FONT_HERSHEY_COMPLEX, 0.8, color, 2)

        # ژست افزایش ولوم: انگشت اشاره به شست
        elif index_distance < threshold and currentTime - lastActionTime > 0.5 and not isMuted:
            volPer = min(volPer + volStep, 100)
            volHistory.append(volPer)
            smoothed_volPer = sum(volHistory) / len(volHistory)
            vol_scalar = smoothed_volPer / 100
            volBar = np.interp(smoothed_volPer, [0, 100], [400, 150])
            try:
                volume.SetMasterVolumeLevelScalar(vol_scalar, None)
            except Exception as e:
                print(f"خطا در تنظیم ولوم: {e}")
            lastActionTime = currentTime
            cv2.putText(img, "Volume Up", (120, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 2)

        # ژست کاهش ولوم: انگشت وسط به شست
        elif middle_distance < threshold and currentTime - lastActionTime > 0.5 and not isMuted:
            volPer = max(volPer - volStep, 0)
            volHistory.append(volPer)
            smoothed_volPer = sum(volHistory) / len(volHistory)
            vol_scalar = smoothed_volPer / 100
            volBar = np.interp(smoothed_volPer, [0, 100], [400, 150])
            try:
                volume.SetMasterVolumeLevelScalar(vol_scalar, None)
            except Exception as e:
                print(f"خطا در تنظیم ولوم: {e}")
            lastActionTime = currentTime
            cv2.putText(img, "Volume Down", (120, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 0, 0), 2)

        # رسم نقاط و خط برای ژست‌های فعال
        if pinky_distance < threshold:
            cv2.circle(img, (thumb_x, thumb_y), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (pinky_x, pinky_y), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (thumb_x, thumb_y), (pinky_x, pinky_y), (255, 0, 255), 2)
        elif index_distance < threshold:
            cv2.circle(img, (thumb_x, thumb_y), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (index_x, index_y), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 2)
        elif middle_distance < threshold:
            cv2.circle(img, (thumb_x, thumb_y), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (middle_x, middle_y), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (thumb_x, thumb_y), (middle_x, middle_y), (255, 0, 255), 2)

    # همگام‌سازی دوره‌ای ولوم (هر 0.5 ثانیه)
    if cTime - pTime > 0.5 and not isMuted:
        volPer = sync_volume()
        pTime = cTime

    # نمایش نوار ولوم
    cv2.rectangle(img, (30, 150), (60, 400), (255, 0, 0), 2)
    cv2.rectangle(img, (30, int(volBar)), (60, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Vol: {int(volPer)}%', (20, 430), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 0), 2)

    # نمایش تصویر
    cv2.imshow("Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# آزادسازی منابع
try:
    cap.release()
    cv2.destroyAllWindows()
except Exception as e:
    print(f"خطا در آزادسازی منابع: {e}")