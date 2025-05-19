# کتابخانه‌های مورد نیاز
<<<<<<< HEAD
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
=======
import cv2  # پردازش تصویر و کار با وبکم
import time  # محاسبه فریم بر ثانیه
import numpy as np  # محاسبات عددی
import HandTrackingModule as htm  # ماژول تشخیص دست
import math  # محاسبات ریاضی
from ctypes import cast, POINTER  # کنترل صدا در ویندوز
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # کنترل صدا

# تنظیمات ابعاد تصویر
wCam, hCam = 640, 480  # عرض و ارتفاع تصویر

# تنظیمات دوربین
cap = cv2.VideoCapture(0)  # اتصال به وبکم پیش‌فرض
cap.set(3, wCam)  # تنظیم عرض تصویر
cap.set(4, hCam)  # تنظیم ارتفاع تصویر
pTime = 0  # زمان قبلی برای محاسبه FPS

# ایجاد شیء تشخیص دست با دقت بالا
detector = htm.handDetector(detectionCon=1)

# بخش کنترل صدا در ویندوز
devices = AudioUtilities.GetSpeakers()  # دریافت دستگاه خروجی صدا
interface = devices.Activate(          # ایجاد رابط کنترل صدا
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))  # تبدیل به شیء قابل استفاده
volRange = volume.GetVolumeRange()  # دریافت محدوده صدا (معمولاً [-65, 0])
minVol = volRange[0]  # حداقل حجم صدا
maxVol = volRange[1]  # حداکثر حجم صدا
vol = 0  # مقدار فعلی صدا
volBar = 400  # موقعیت اولیه نوار صدا
volPer = 0  # درصد صدا

# حلقه اصلی برنامه
while True:
    success, img = cap.read()  # دریافت فریم از دوربین
    if not success:  # اگر دریافت فریم ناموفق بود
        break  # خروج از حلقه
    
    # تشخیص دست در تصویر
    img = detector.findHands(img)
    # دریافت موقعیت نقاط دست (بدون رسم)
    lmList, _ = detector.findPosition(img, draw=False)
    
    # اگر دست تشخیص داده شد
    if len(lmList) != 0:
        # بررسی وجود نقاط کلیدی (نوک انگشتان)
        if len(lmList) > 8:  # نیاز به حداقل 9 نقطه داریم
            # مختصات نوک انگشت شست (نقطه 4) و انگشت اشاره (نقطه 8)
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            # محاسبه نقطه میانی
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # رسم نقاط و خط بین انگشتان
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)  # شست
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)  # اشاره
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)  # خط اتصال
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)  # نقطه میانی

            # محاسبه فاصله بین دو انگشت
            length = math.hypot(x2 - x1, y2 - y1)
            
            # تبدیل فاصله به محدوده صدا
            # محدوده دست: 50-300 پیکسل → محدوده صدا: minVol تا maxVol
            vol = np.interp(length, [50, 300], [minVol, maxVol])
            volBar = np.interp(length, [50, 300], [400, 150])  # برای نمایش بصری
            volPer = np.interp(length, [50, 300], [0, 100])  # درصد صدا
            
            # تنظیم صدا فقط در صورت تغییر محسوس (برای بهینه‌سازی)
            if abs(volume.GetMasterVolumeLevel() - vol) > 1:
                volume.SetMasterVolumeLevel(vol, None)

            # تغییر رنگ نقطه میانی وقتی فاصله کم است (حالت بسته)
            if length < 50:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

    # رسم نوار حجم صدا
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)  # قاب نوار
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)  # سطح صدا
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)  # نمایش درصد صدا

    # محاسبه و نمایش FPS
>>>>>>> 78b77036812a7e02d71bdf66130f0db947a8b1cd
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 0), 2)

<<<<<<< HEAD
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
=======
    cv2.imshow("Img", img)  # نمایش تصویر
    if cv2.waitKey(1) & 0xFF == ord('q'):  # خروج با فشار کلید q
        break

# آزادسازی منابع
cap.release()  # آزاد کردن دوربین
cv2.destroyAllWindows()  # بستن تمام پنجره‌ها
>>>>>>> 78b77036812a7e02d71bdf66130f0db947a8b1cd
