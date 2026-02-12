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

# Scroll sensitivity settings - hybrid mode
scroll_amount_up_base = 18  # Base scroll up (see earlier content) - almost none
scroll_amount_down_base = 500  # Base scroll down (see later content)
scroll_speed_multiplier = 5000  # Multiplier for speed-based scrolling
swipe_threshold_finger_down = 0.39  # Finger moves down to scroll up (very hard to trigger)
swipe_threshold_finger_up = 0.04  # Finger moves up to scroll down (more sensitive)

# Continuous mode settings
continuous_sensitivity_up = 200  # Continuous scrolling sensitivity for up (very low)
continuous_sensitivity_down = 53  # Continuous scrolling sensitivity for down (almost none)
slow_movement_threshold = 0.01  # If movement per frame is below this, it's "slow"
slow_movement_threshold_down = 0.0005  # Extremely slow required for continuous down (almost impossible)
deadzone = 0.003  # Minimum movement for continuous mode

# Variables to track gesture state
gesture_start_y = None
gesture_start_frame = 0
current_frame = 0
gesture_in_progress = False
cooldown_frames = 0
cooldown_duration = 10  # Frames to wait before detecting next gesture
previous_hand_y = None
continuous_mode = False

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
    cv2.putText(img, "Move INDEX FINGER up/down to scroll", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Decrease cooldown counter
    if cooldown_frames > 0:
        cooldown_frames -= 1
        cv2.putText(img, "Cooldown...", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on the camera feed
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get the y-coordinate of the index finger tip (Landmark 8)
            current_hand_y = hand_landmarks.landmark[8].y
            
            # Highlight the index finger tip being tracked
            finger_tip = hand_landmarks.landmark[8]
            cx, cy = int(finger_tip.x * w), int(finger_tip.y * h)
            cv2.circle(img, (cx, cy), 15, (0, 255, 255), -1)  # Yellow circle on finger tip
            
            # Only process gestures if not in cooldown
            if cooldown_frames == 0:
                # Start tracking a new gesture
                if gesture_start_y is None:
                    gesture_start_y = current_hand_y
                    gesture_start_frame = current_frame
                    previous_hand_y = current_hand_y
                    gesture_in_progress = True
                    continuous_mode = False
                    cv2.putText(img, "Ready to swipe", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Check if gesture has moved enough to trigger scroll
                elif gesture_in_progress:
                    delta_y = current_hand_y - gesture_start_y
                    frame_delta = abs(current_hand_y - previous_hand_y) if previous_hand_y else 0
                    
                    # Calculate swipe speed (distance per frame)
                    frames_elapsed = current_frame - gesture_start_frame
                    swipe_speed = abs(delta_y) / max(frames_elapsed, 1)
                    
                    # Determine if movement is slow (different thresholds for up/down)
                    is_slow_movement_up = frame_delta < slow_movement_threshold and frame_delta > deadzone and delta_y < 0
                    is_slow_movement_down = frame_delta < slow_movement_threshold_down and frame_delta > deadzone and delta_y > 0
                    is_slow_movement = is_slow_movement_up or is_slow_movement_down
                    
                    # If not in continuous mode yet, check for discrete swipe thresholds
                    if not continuous_mode:
                        # Finger moved down - scroll up (speed-based)
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
                        
                        # Finger moved up - scroll down (speed-based)
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
                        
                        # Activate continuous mode if moving slowly and past threshold
                        elif is_slow_movement and (abs(delta_y) > swipe_threshold_finger_down or abs(delta_y) > swipe_threshold_finger_up):
                            continuous_mode = True
                            cv2.putText(img, "Continuous mode ON (slow movement)", (10, 70), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                        
                        # Still tracking gesture
                        else:
                            cv2.putText(img, f"Track... d:{delta_y:.3f} spd:{swipe_speed:.3f}", (10, 70), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Continuous mode active - scroll based on finger movement
                    else:
                        if frame_delta > deadzone:
                            current_delta = current_hand_y - previous_hand_y
                            
                            # Finger moving down = scroll up
                            if current_delta > 0:
                                scroll_amount = int(current_delta * continuous_sensitivity_up)
                                pyautogui.scroll(scroll_amount)
                                cv2.putText(img, f"Continuous UP: {scroll_amount}", (10, 70), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            # Finger moving up = scroll down
                            elif current_delta < 0:
                                scroll_amount = int(current_delta * continuous_sensitivity_down)
                                pyautogui.scroll(scroll_amount)
                                cv2.putText(img, f"Continuous DOWN: {scroll_amount}", (10, 70), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        else:
                            cv2.putText(img, "Continuous - Stable", (10, 70), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
                    
                    previous_hand_y = current_hand_y
            
            break  # Only track the first hand detected
    else:
        # Reset gesture when hand is removed
        gesture_start_y = None
        gesture_in_progress = False
        previous_hand_y = None
        continuous_mode = False
        cv2.putText(img, "No hand detected", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Show the camera feed window
    cv2.imshow("Lazy Scroller", img)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()