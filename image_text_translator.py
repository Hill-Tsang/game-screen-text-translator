import os
import sys
import cv2
import time
import keyboard
import numpy as np
from functools import wraps
from windows_capture import WindowsCapture, Frame, InternalCaptureControl

from src.translator import Translator
from src.image_processor import ImageProcessor
from src.google_cloud_translator import GoogleCloudTranslator

recog_network = "japanese_g2_trained"   # "standard" or "name of custom model"

def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    return wrapper

def crop_frame(frame):
    crop_x = frame.width // 8

    start_width = 0 + crop_x
    end_width = frame.width - crop_x

    cropped_frame = frame.crop(start_width, 0, end_width, frame.height)

    return cropped_frame

def translate_text_on_image(img, image_processor, translator):
    global live_capture
    global previous_texts
    global translated
    global new_texts

    # Extract text and coordinates from the image
    texts, coordinates = image_processor.extract_text(img)

    # Translate only when same texts are extracted in 2 consecutive frames
    if live_capture:
        if texts != previous_texts:
            if new_texts:
                previous_texts = texts
                translated = False
            else:
                new_texts = True
            return
        else:
            new_texts = False
            if translated:
                return
    
    # Get text boxes, colors, and assign extracted texts to groups
    text_boxes, text_box_colors = image_processor.get_text_box(img, texts, coordinates)
    text_groups = image_processor.get_text_groups(img, texts, coordinates, text_boxes, text_box_colors)

    # Translate
    romaji_texts = translator.batch_translate("ja", "romaji", text_groups)
    if googlecloud_translator:
        translated_texts = googlecloud_translator.translate("ja", "zh-TW", text_groups)
    else:
        translated_texts = translator.batch_translate("ja", "zh-TW", text_groups)
    
    for i in range(len(text_groups)):
        print(f"{'Original:':<12}{text_groups[i]}")
        print(f"{'Romaji:':<12}{romaji_texts[i]}")
        if googlecloud_translator:
            print(f"{'Translated:':<12}{translated_texts[i].translated_text}")
        else:
            print(f"{'Translated:':<12}{translated_texts[i]}")
        print(" ")
    if texts:
        print("---------------------------------")
        print("")

    translated = True

image_processor = ImageProcessor("ja", recog_network)

try:
    with open('project_id.txt', 'r') as file:
        PROJECT_ID = file.read()
        googlecloud_translator = GoogleCloudTranslator(PROJECT_ID)
except:
    googlecloud_translator = None

translator = Translator()

live_capture = False
previous_texts = []
translated = False
new_texts = False

# Image file text extraction and translation
if len(sys.argv) == 2:
    if os.path.isfile(sys.argv[1]):
        img = cv2.imread(sys.argv[1])
        translate_text_on_image(img, image_processor, translator)
    elif os.path.isdir(sys.argv[1]):
        for file in os.listdir(sys.argv[1]):
            img = cv2.imread(os.path.join(sys.argv[1], file))
            translate_text_on_image(img, image_processor, translator)
            
            print("Press Enter to continue...")
            keyboard.wait("enter")
    else:
        print(f"Can't open image file: {sys.argv[1]}")
# Runtime game screen text extraction and translation
else:
    window_title = "Projector - Source: GC573"

    capture = WindowsCapture(window_name=window_title)

    live_capture = True

    @capture.event
    def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
        cropped_frame = crop_frame(frame)

        img = np.array(cropped_frame.frame_buffer)
        #frame.save_as_image("screenshot.png")
        capture_control.stop() # Stop after one frame
        
        translate_text_on_image(img, image_processor, translator)
                
    @capture.event
    def on_closed():
        print("Capture Session Closed")

    while True:
        capture.start()
        time.sleep(0.5)