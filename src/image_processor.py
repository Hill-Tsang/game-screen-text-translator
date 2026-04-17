import cv2
import sys
import string
import easyocr
import numpy as np
from PIL import ImageFont, ImageDraw, Image

class ImageProcessor():
    
    def __init__(self, language, recog_network):
        print("Init Image processor")
        self.reader = easyocr.Reader([language], gpu=True, recog_network=recog_network)
        self.font_path = "C:/Windows/Fonts/meiryo.ttc"
        self.font_size = 60
        self.font_color = (0, 0, 0)
        self.resize_width = 800
        self.step = 5
        self.color_similarity_threshold = 0.2
        self.sentence_box_scale = 0.8

    def reduce_img_color(self, img):
        div = 64    # Factor of reduction
        img = (img // div) * div + (div // 2)
        return img
    
    def extract_text(self, img):
        result = self.reader.readtext(img)
        skip_chars = string.ascii_letters + string.digits + string.punctuation

        texts = []    # Extracted text list separated by newline
        coordinates = [] # [[tl, br, center]]

        for (bbox, text, prob) in result:
            if prob <= 0.1:
                continue    # Skip text with high uncertainty

            if all(c in skip_chars for c in text):
                continue    # Skip English letters and digits and punctuation
            
            (tl, tr, br, bl) = bbox

            tl = (int(tl[0]), int(tl[1])) # Top left xy
            br = (int(br[0]), int(br[1])) # Bottom right xy
            center = (int((br[0]-tl[0])/2 + tl[0]), int((br[1]-tl[1])/2 + tl[1])) # Center xy

            texts.append(text)
            coordinates.append([tl, br, center])

        return texts, coordinates
    
    def get_text_box_color(self, img, tl, br):
        left_line = img[tl[1]:br[1], tl[0]:tl[0]+1]
        unique, counts = np.unique(left_line, axis=0, return_counts=True)
        most_frequent_color = unique[np.argmax(counts)]

        return most_frequent_color
    
    def walk_to_get_border(self, img, starting_coordinate, direction, text_box_color):
        new_point = starting_coordinate
        h, w = img.shape[:2]

        if direction == "up":
            max_length = h
            step = -self.step
            coor_index = 1
        elif direction == "down":
            max_length = h
            step = self.step
            coor_index = 1
        elif direction == "left":
            max_length = w
            step = -self.step
            coor_index = 0
        elif direction == "right":
            max_length = w
            step = self.step
            coor_index = 0

        i = 0
        while True:
            if 0 < new_point[coor_index] < max_length:
                new_point_color = img[new_point[1], new_point[0]]
                if np.array_equal(new_point_color, text_box_color):
                    new_point[coor_index] += step
                    i += step
                elif np.linalg.norm(text_box_color - new_point_color) / 447.67 < self.color_similarity_threshold:
                    new_point[coor_index] += step
                    i += step
                else:
                    new_point[coor_index] -= step
                    break
            else:
                new_point[coor_index] -= step
                break
        
        return new_point

    def get_text_box(self, img, texts, coordinates):
        text_boxes = []   # [[tl br], [tl br]]
        text_box_colors = []

        for i in range(len(texts)):
            x_left = coordinates[i][0][0]
            y_center = coordinates[i][2][1]

            text_bg_color = self.get_text_box_color(img, coordinates[i][0], coordinates[i][1])

            # Check if text is inside any box
            new_box = True
            for j in range(len(text_boxes)):
                if (text_boxes[j][0][0] < x_left < text_boxes[j][1][0]) and (text_boxes[j][0][1] < y_center < text_boxes[j][1][1]):
                    if (text_bg_color == text_box_colors[j]).all():
                        new_box = False
                        break
            if not new_box:
                continue
            
            # Main color of the box
            text_box_colors.append(text_bg_color)

            # Use top left coordinate of the text as starting point
            if (img[coordinates[i][0][1], coordinates[i][0][0]] == text_bg_color).all():
                top_xy = self.walk_to_get_border(img, [coordinates[i][0][0], coordinates[i][0][1]], "up", text_bg_color)
            # Use middle left coordinate of the text as starting point
            else:
                top_xy = self.walk_to_get_border(img, [x_left, y_center], "up", text_bg_color)
  
            topleft_xy = self.walk_to_get_border(img, top_xy.copy(), "left", text_bg_color)
            topright_xy = self.walk_to_get_border(img, topleft_xy.copy(), "right", text_bg_color)
            bottomright_xy = self.walk_to_get_border(img, topright_xy.copy(), "down", text_bg_color)

            # If the detected box is smaller than the text, use the text coordinate as the box
            box_width = topright_xy[0] - topleft_xy[0]
            box_height = bottomright_xy[1] - topleft_xy[1]
            text_width = coordinates[i][1][0] - coordinates[i][0][0]
            text_height = coordinates[i][1][1] - coordinates[i][0][1]
            if box_width < text_width or box_height < text_height: 
                text_boxes.append([coordinates[i][0], coordinates[i][1]])
            else:
                text_boxes.append([topleft_xy, bottomright_xy])

        return text_boxes, text_box_colors
    
    def get_text_groups(self, img, texts, coordinates, text_boxes, text_box_colors):
        max_height, max_width = img.shape[:2]
        
        text_groups = []
        for box in text_boxes:
            text_groups.append([])
        
        for i in range(len(texts)):
            center = coordinates[i][2]

            # Find the corresponding box of the text
            for j in range(len(text_boxes)):
                top = text_boxes[j][0][1]
                bottom = text_boxes[j][1][1]
                left = text_boxes[j][0][0]
                right = text_boxes[j][1][0]
                if left <= center[0] <= right and top <= center[1] <= bottom:
                    if (img[coordinates[i][0][1], coordinates[i][0][0]] == text_box_colors[j]).all():
                        text_groups[j].append(texts[i])
                        break
                    if (img[coordinates[i][2][1], coordinates[i][0][0]] == text_box_colors[j]).all():
                        text_groups[j].append(texts[i])
                        break
        
        # Join words in the same box for faster translation
        for i in range(len(text_boxes)):
            if text_boxes[i][1][0] - text_boxes[i][0][0] > max_width * self.sentence_box_scale:
                sentence = " ".join(text_groups[i])
                text_groups[i] = sentence
            else:
                sentence = "，".join(text_groups[i])
                text_groups[i] = sentence

        return text_groups

    def overlay_translated_text(self, image_np, text, point):
        # Convert from BGR (OpenCV) to RGB (PIL)
        image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(image_pil)
        
        try:
            font = ImageFont.truetype(self.font_path, self.font_size, encoding="utf-8")
        except IOError:
            print(f"Error: Could not open font file {self.font_path}.")
            return image_np # Return original image on failure
        
        # PIL uses RGB colors, so convert BGR color to RGB
        color_rgb = (self.font_color[2], self.font_color[1], self.font_color[0])
        
        draw.text(point, text, font=font, fill=color_rgb)
        
        # Convert back from RGB (PIL) to BGR (OpenCV)
        image_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

        return image_bgr

    def show_image(self, img, wait_key=True, texts=None, coordinates=None, text_boxes=None):
        overlay = img.copy()
        
        if texts:
            for i in range(len(texts)):
                img = self.overlay_translated_text(img, texts[i], coordinates[i])
        
        if text_boxes:
            for box in text_boxes:
                cv2.rectangle(img, box[0], box[1], (0, 0, 0), 4)

        if coordinates:
            for coor in coordinates:
                cv2.rectangle(overlay, coor[0], coor[1], (0, 0, 255), -1)
        
        alpha = 0.5
        result = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        h, w = img.shape[:2]
        resize_height = int(h * (self.resize_width / w))
        resize_img = cv2.resize(result, (self.resize_width, resize_height), interpolation=cv2.INTER_AREA)
        cv2.imshow("Captured Window", resize_img)

        if wait_key:
            cv2.waitKey(0)
            cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        try:
            image = cv2.imread(sys.argv[1])
        except:
            print(f"Could not open image file {sys.argv[1]}")

        image_processor = ImageProcessor("ja", recog_network="japanese_g2_trained")

        texts, coordinates = image_processor.extract_text(image)

        print(len(texts))
        print(texts)

        print(len(coordinates))
        print(coordinates)

        adjusted_image = image_processor.reduce_img_color(image)

        text_boxes, text_box_colors = image_processor.get_text_box(adjusted_image, texts, coordinates)
        print(f"{len(text_boxes)} text_boxes")
        print(text_boxes)

        text_groups = image_processor.get_text_groups(adjusted_image, texts, coordinates, text_boxes, text_box_colors)
        print("text_groups")
        print(text_groups)

        image_processor.show_image(image, coordinates=coordinates, text_boxes=text_boxes)