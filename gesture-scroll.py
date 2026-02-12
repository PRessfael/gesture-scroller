import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.3,  # Lower threshold for better far-distance detection
    min_tracking_confidence=0.3,   # Lower threshold to maintain tracking when far
    model_complexity=1              # Use full model for better detection accuracy
)
mp_draw = mp.solutions.drawing_utils

# Initialize Camera
cap = cv2.VideoCapture(0)

# Scroll sensitivity settings
scroll_amount_up_base = 500  # Base scroll up (see earlier content) - same as scroll down
scroll_amount_down_base = 500  # Base scroll down (see later content)
scroll_speed_multiplier = 5000  # Multiplier for speed-based scrolling
swipe_threshold_finger_down = 0.15  # Finger moves down to scroll up (less sensitive, requires more movement)
swipe_threshold_finger_up = 0.04  # Finger moves up to scroll down (more sensitive)

# Variables to track gesture state
gesture_start_y = None  # For index finger
gesture_start_frame = 0
middle_gesture_start_y = None  # For middle finger
middle_gesture_start_frame = 0
current_frame = 0
gesture_in_progress = False
middle_gesture_in_progress = False
cooldown_frames = 0
middle_cooldown_frames = 0
cooldown_duration = 10  # Frames to wait before detecting next gesture
previous_hand_y = None
previous_middle_finger_y = None

# Function to detect if hand is making a fist
def is_fist(hand_landmarks):
    
    fingers_closed = 0
    
    # Check index finger
    if hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y:
        fingers_closed += 1
    
    # Check middle finger
    if hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y:
        fingers_closed += 1
    
    # Check ring finger
    if hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y:
        fingers_closed += 1
    
    # Check pinky finger
    if hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y:
        fingers_closed += 1
    
    # Consider it a fist if at least 3 out of 4 fingers are closed
    return fingers_closed >= 3

# Main Loop
while True:
    success, img = cap.read()
    if not success:
        break
    
    current_frame += 1

    # Flip image horizontally for a mirror effect (more natural interaction)
    img = cv2.flip(img, 1)
    
    # Convert BGR image to RGB for MediaPipe
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Process the frame and detect hands
    results = hands.process(img_rgb)
    
    # Get frame dimensions
    h, w, c = img.shape
    
    # Add instructions on screen
    cv2.putText(img, "INDEX: swipe scroll | MIDDLE: swipe scroll up", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Decrease cooldown counter
    if cooldown_frames > 0:
        cooldown_frames -= 1
        cv2.putText(img, "Cooldown...", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
    
    if middle_cooldown_frames > 0:
        middle_cooldown_frames -= 1
        cv2.putText(img, "Middle Cooldown...", (10, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on the camera feed
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get the y-coordinate of the index finger tip (Landmark 8) for discrete scroll
            current_hand_y = hand_landmarks.landmark[8].y
            
            # Get the y-coordinate of the middle finger tip (Landmark 12) for discrete scroll up
            current_middle_finger_y = hand_landmarks.landmark[12].y
            
            # Highlight the index finger tip being tracked
            index_finger_tip = hand_landmarks.landmark[8]
            ix, iy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
            cv2.circle(img, (ix, iy), 15, (0, 255, 255), -1)  # Yellow circle on index finger
            
            # Highlight the middle finger tip being tracked
            middle_finger_tip = hand_landmarks.landmark[12]
            mx, my = int(middle_finger_tip.x * w), int(middle_finger_tip.y * h)
            cv2.circle(img, (mx, my), 15, (0, 255, 0), -1)  # Green circle on middle finger
            
            # MIDDLE FINGER: Discrete swipe scroll up (same as scroll down values)
            if middle_cooldown_frames == 0:
                # Start tracking middle finger gesture
                if middle_gesture_start_y is None:
                    middle_gesture_start_y = current_middle_finger_y
                    middle_gesture_start_frame = current_frame
                    previous_middle_finger_y = current_middle_finger_y
                    middle_gesture_in_progress = True
                    cv2.putText(img, "Middle ready", (10, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Check if middle finger moved down to scroll up
                elif middle_gesture_in_progress:
                    middle_delta_y = current_middle_finger_y - middle_gesture_start_y
                    
                    # Calculate swipe speed
                    middle_frames_elapsed = current_frame - middle_gesture_start_frame
                    middle_swipe_speed = abs(middle_delta_y) / max(middle_frames_elapsed, 1)
                    
                    # Middle finger moved down - scroll up (same values as scroll down)
                    if middle_delta_y > swipe_threshold_finger_down:
                        scroll_amount = int(scroll_amount_down_base + (middle_swipe_speed * scroll_speed_multiplier))
                        pyautogui.scroll(scroll_amount)
                        cv2.putText(img, f"MIDDLE SCROLL UP: {scroll_amount} (speed: {middle_swipe_speed:.3f})", (10, 100), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        middle_gesture_start_y = None
                        middle_gesture_in_progress = False
                        previous_middle_finger_y = None
                        middle_cooldown_frames = cooldown_duration
                    
                    # Still tracking middle finger gesture
                    else:
                        cv2.putText(img, f"Middle track... d:{middle_delta_y:.3f}", (10, 100), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    previous_middle_finger_y = current_middle_finger_y
            
            # INDEX FINGER: Discrete swipe scrolling (only if not in cooldown)
            if cooldown_frames == 0:
                # Start tracking a new gesture
                if gesture_start_y is None:
                    gesture_start_y = current_hand_y
                    gesture_start_frame = current_frame
                    previous_hand_y = current_hand_y
                    gesture_in_progress = True
                    cv2.putText(img, "Ready to swipe", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Check if gesture has moved enough to trigger scroll
                elif gesture_in_progress:
                    delta_y = current_hand_y - gesture_start_y
                    
                    # Calculate swipe speed (distance per frame)
                    frames_elapsed = current_frame - gesture_start_frame
                    swipe_speed = abs(delta_y) / max(frames_elapsed, 1)
                    
                    # Index finger moved down - scroll up (speed-based)
                    if delta_y > swipe_threshold_finger_down:
                        # Calculate scroll amount based on speed
                        scroll_amount = int(scroll_amount_up_base + (swipe_speed * scroll_speed_multiplier))
                        pyautogui.scroll(scroll_amount)
                        cv2.putText(img, f"SCROLL UP: {scroll_amount} (speed: {swipe_speed:.3f})", (10, 70), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        gesture_start_y = None
                        gesture_in_progress = False
                        previous_hand_y = None
                        cooldown_frames = cooldown_duration
                    
                    # Index finger moved up - scroll down (speed-based)
                    elif delta_y < -swipe_threshold_finger_up:
                        # Calculate scroll amount based on speed
                        scroll_amount = int(scroll_amount_down_base + (swipe_speed * scroll_speed_multiplier))
                        pyautogui.scroll(-scroll_amount)
                        cv2.putText(img, f"SCROLL DOWN: {scroll_amount} (speed: {swipe_speed:.3f})", (10, 70), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        gesture_start_y = None
                        gesture_in_progress = False
                        previous_hand_y = None
                        cooldown_frames = cooldown_duration
                    
                    # Still tracking gesture
                    else:
                        cv2.putText(img, f"Track... d:{delta_y:.3f} spd:{swipe_speed:.3f}", (10, 70), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    previous_hand_y = current_hand_y
            
            break  # Only track the first hand detected
    else:
        # Reset gesture when hand is removed
        gesture_start_y = None
        gesture_in_progress = False
        previous_hand_y = None
        middle_gesture_start_y = None
        middle_gesture_in_progress = False
        previous_middle_finger_y = None
        cv2.putText(img, "No hand detected", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Show the camera feed window
    cv2.imshow("Lazy Scroller", img)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()