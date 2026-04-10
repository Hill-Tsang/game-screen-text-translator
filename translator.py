import easyocr
import cv2
import numpy as np
import time
from deep_translator import GoogleTranslator
from windows_capture import WindowsCapture, Frame, InternalCaptureControl
import csv
from PIL import ImageFont, ImageDraw, Image
import sys
import os
from functools import wraps
import keyboard

SHOW_CAPTURED_WINDOW = False
TRANSLATE_EACH_WORD = False

def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    return wrapper

# Parse romaji csv into dict. E.g. dict["あ"] = a
def load_romaji_csv(file_path):
    dict = {}
    with open(file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        
        for row in csv_reader:
            dict[row[0]] = row[1]

    return dict

def crop_frame(frame):
    crop_x = frame.width // 8

    start_width = 0 + crop_x
    end_width = frame.width - crop_x

    cropped_frame = frame.crop(start_width, 0, end_width, frame.height)

    return cropped_frame

def extract_text(img):
    global previous_text_list
    global new_text_list

    result = reader.readtext(img)

    new_text_list = [""]

    # Print the detected text and optionally the bounding boxes
    old_br = 0
    for (bbox_a, text, prob) in result:
        (tl, tr, br, bl) = bbox_a

        tl = (int(tl[0]), int(tl[1])) # Top left xy
        br = (int(br[0]), int(br[1])) # Bottom right xy

        if tl[0] < old_br:
            new_text_list.append(text)
        else:
            new_text_list[-1] = new_text_list[-1] + " " + text
        old_br = br[0]

        # Optional: Draw bounding boxes on the image
        #cv2.rectangle(img, tl, br, (0, 255, 0), 2)
        cv2.rectangle(img, tl, br, (0, 255, 0), -1)    # Filled rectangle

        if SHOW_CAPTURED_WINDOW:
            img = put_japanese_text(img, text, tl, font_path_example, font_size, text_color)
            
            # Draw captured screen
            h, w = img.shape[:2]
            new_w = 600
            new_h = int(h * (new_w / w))
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            cv2.imshow("Captured Window", resized)

def put_japanese_text(image_np, text, point, font_path, font_size, color):
    """
    Draws Japanese text on an OpenCV image using PIL.

    Args:
        image_np (numpy.ndarray): The OpenCV image (BGR format).
        text (str): The Japanese text to draw (e.g., "こんにちは世界").
        point (tuple): The (x, y) coordinates for the top-left corner of the text.
        font_path (str): Path to a Japanese TrueType font file (.ttf).
        font_size (int): Font size.
        color (tuple): Text color in BGR format (e.g., (0, 0, 255) for red).
    
    Returns:
        numpy.ndarray: The image with text drawn (OpenCV BGR format).
    """

    # Convert from BGR (OpenCV) to RGB (PIL)
    image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(image_pil)
    
    try:
        font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    except IOError:
        print(f"Error: Could not open font file {font_path}.")
        return image_np # Return original image on failure
    
    # PIL uses RGB colors, so convert BGR color to RGB
    color_rgb = (color[2], color[1], color[0])
    
    draw.text(point, text, font=font, fill=color_rgb)
    
    # Convert back from RGB (PIL) to BGR (OpenCV)
    image_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

    return image_bgr

@time_it
def translate():
    global new_text_list
    global previous_text_list

    if not new_text_list or new_text_list == previous_text_list:
        return

    for line in new_text_list:
        print(line)
        roma_line = ""

        consonant = False

        for char in line:
            if char == "っ" or char == "ッ":
                consonant = True
                continue
            
            if char == "は":
                if roma_line and roma_line[-1] != " ":
                    roma_char = "wa"
                else:
                    roma_char = romaji_dict.get(char)
            else:
                roma_char = romaji_dict.get(char)
            
            if roma_char is not None:
                if consonant:
                    roma_line += romaji_dict[char][0]
                    consonant = False

                roma_line += roma_char
            else:
                roma_line += char

        translated_line = ""
        if TRANSLATE_EACH_WORD:
            for word in line.split(" "):
                translated_word = translator.translate(word)
                translated_line = translated_line + translated_word + " "
        
        print(roma_line)
        if TRANSLATE_EACH_WORD:
            print(translated_line)
        romaji_text_list.append(roma_line)

    jp_full_text = " ".join(new_text_list)
    try:
        translated = translator.translate(jp_full_text)
        print(translated)

        #translated = translator.translate_batch(new_text_list)
        #print(translated)
    except:
        print("Can't translate")

    previous_text_list = new_text_list

    #translated = GoogleTranslator(source='ja', target='en').translate(jp_full_text)
    #print(translated)
    
    #jp_full_text = "\n".join(new_text_list)
    #translated = translator.translate(jp_full_text)
    #print(translated)
    print("---------------------------------")
    print("")

previous_text_list = []    # Previous extracted text separated by newline
new_text_list = [""]    # New extracted text separated by newline
romaji_text_list = []

# Load japanese character and its romaji
romaji_dict = load_romaji_csv("romaji.csv")

# Parameters used for drawing extracted/translated text on image
font_path_example = "C:/Windows/Fonts/meiryo.ttc"
font_size = 60
text_color = (0, 0, 0)

print("Init EasyOCR reader")
reader = easyocr.Reader(['ja'], gpu=True)

print("Init translator")
translator = GoogleTranslator(source='ja', target='zh-TW')

# Image file text extraction and translation
if len(sys.argv) == 2:
    if os.path.isfile(sys.argv[1]):
        image = cv2.imread(sys.argv[1])
        extract_text(image)
        translate()
        if SHOW_CAPTURED_WINDOW:
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    elif os.path.isdir(sys.argv[1]):
        for file in os.listdir(sys.argv[1]):
            image = cv2.imread(os.path.join(sys.argv[1], file))
            extract_text(image)
            translate()
            if SHOW_CAPTURED_WINDOW:
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
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
        global new_text_list
        global previous_text_list

        cropped_frame = crop_frame(frame)

        img = np.array(cropped_frame.frame_buffer)
        #frame.save_as_image("screenshot.png")
        capture_control.stop() # Stop after one frame
        
        extract_text(img)

        translate()
                
    @capture.event
    def on_closed():
        print("Capture Session Closed")

    while True:
        capture.start()
        time.sleep(0.5)