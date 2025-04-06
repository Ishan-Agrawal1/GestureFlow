import cv2
import mediapipe as mp
import pyautogui
import webbrowser
import time
import math

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils


# Try to find working webcam index
working_cam = None
for i in range(3):  # Try camera 0, 1, 2
    test_cap = cv2.VideoCapture(i)
    if test_cap.isOpened():
        success, _ = test_cap.read()
        if success:
            working_cam = i
            test_cap.release()
            break
    test_cap.release()

if working_cam is None:
    print("❌ Error: Could not find any working webcam.")
    exit()

# Use the found camera
cap = cv2.VideoCapture(working_cam)
print(f"✅ Using webcam index: {working_cam}")

# Flags
browser_opened = False
kaido_opened = False
last_switch_time = 0
google_last_time = 0  # Cooldown for Google

# Count fingers function
def count_fingers(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other fingers
    for id in range(1, 5):
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return sum(fingers)

# Distance function (for 👌)
def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

# Main loop
while True:
    success, image = cap.read()
    if not success:
        print("❌ Couldn't read frame from webcam.")
        break

    image = cv2.flip(image, 1)
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand_landmarks)

            # 👌 Gesture: Thumb tip & Index tip touching = Open Instagram (kaido.tv replacement)
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            thumb_index_distance = distance(thumb_tip, index_tip)

            if thumb_index_distance < 0.04 and not kaido_opened:
                webbrowser.open("https://instagram.com/")
                kaido_opened = True
                cv2.putText(image, "👌 Opening Instagram", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 128, 255), 2)
            elif thumb_index_distance >= 0.05:
                kaido_opened = False  # Reset when fingers separate

            # 👉 3 fingers up = Switch tab
            if finger_count == 3:
                current_time = time.time()
                if current_time - last_switch_time > 1:
                    pyautogui.hotkey('ctrl', 'tab')
                    cv2.putText(image, "Switching Tab", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (128, 0, 255), 3)
                    last_switch_time = current_time

            # ✋ 5 fingers = Scroll Down (like next reel)
            elif finger_count == 5:
                cv2.putText(image, "Scroll Down (Next)", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                pyautogui.scroll(-50)

            # ✊ Fist (0 fingers) = Scroll Up (like previous reel)
            elif finger_count == 0:
                cv2.putText(image, "Scroll Up (Previous)", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                pyautogui.scroll(50)

            # ✌️ 2 fingers = Open Google (with cooldown)
            elif finger_count == 2:
                current_time = time.time()
                if current_time - google_last_time > 3:
                    webbrowser.open("https://www.google.com")
                    google_last_time = current_time
                    cv2.putText(image, "Opening Google", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

    cv2.imshow("GestureMate - ML Project", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()