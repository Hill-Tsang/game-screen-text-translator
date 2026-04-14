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

@time_it
def translate_text_on_image(img, image_processor, translator):
    global previous_texts

    texts, coordinates = image_processor.extract_text(img)

    if texts == previous_texts:
        return

    previous_texts = texts

    text_boxes = image_processor.get_text_box(image, texts, coordinates)
    text_groups = image_processor.get_text_groups(image, texts, coordinates, text_boxes)

    for text_group in text_groups:
        for sentence in text_group:
            translator.translate(sentence)
            print(" ")

    print("---------------------------------")
    print("")

image_processor = ImageProcessor("ja")

translator = Translator("ja", "zh-TW")

previous_texts = []

# Image file text extraction and translation
if len(sys.argv) == 2:
    if os.path.isfile(sys.argv[1]):
        image = cv2.imread(sys.argv[1])
        translate_text_on_image(image, image_processor, translator)
    elif os.path.isdir(sys.argv[1]):
        for file in os.listdir(sys.argv[1]):
            image = cv2.imread(os.path.join(sys.argv[1], file))
            translate_text_on_image(image, image_processor, translator)
            
            print("Press Enter to continue...")
            keyboard.wait("enter")
    else:
        print(f"Can't open image file: {sys.argv[1]}")
# Runtime game screen text extraction and translation
else:
    window_title = "Projector - Source: GC573"

    capture = WindowsCapture(window_name=window_title)

    @capture.event
    def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
        cropped_frame = crop_frame(frame)

        img = np.array(cropped_frame.frame_buffer)
        #frame.save_as_image("screenshot.png")
        capture_control.stop() # Stop after one frame
        
        translate_text_on_image(image, image_processor, translator)
                
    @capture.event
    def on_closed():
        print("Capture Session Closed")

    while True:
        capture.start()
        time.sleep(0.5)