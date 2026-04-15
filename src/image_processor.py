import cv2
import sys
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
        self.step = 1

    def get_text_box(self, img, texts, coordinates):
        # Reduce color for better box detection
        div = 64    # Factor of reduction
        img = (img // div) * div + (div // 2)

        max_height, max_width = img.shape[:2]
        
        text_boxes = []   # [[tl br], [tl br]]

        for i in range(len(texts)):
            tl = coordinates[i][0]

            # Check if text is inside any box
            new_box = True
            for box in text_boxes:
                if tl[0] > box[0][0] and tl[0] < box[1][0] and tl[1] > box[0][1] and tl[1] < box[1][1]:
                    new_box = False
            if not new_box:
                continue
            
            # Main color of the box
            color = img[int(tl[1]), int(tl[0])]

            # Move upward to find top coordinate
            distance = 0
            while True:
                if int(tl[1]) - distance < 0:
                    distance -= self.step
                    break
                elif np.array_equal(img[int(tl[1])-distance, int(tl[0])], color):
                    distance += self.step
                else:
                    distance -= self.step
                    break
            top_xy = (int(tl[0]), int(tl[1])-distance)
            
            # Move left to find top left coordinate
            distance = 0
            while True:
                if top_xy[0] - distance < 0:
                    distance -= self.step
                    break
                elif (img[top_xy[1], top_xy[0]-distance] == color).all():
                    distance += self.step
                else:
                    distance -= self.step
                    break
            topleft_xy = (top_xy[0]-distance, top_xy[1])

            # Move right to find top right coordinate
            distance = 0
            while True:
                if top_xy[0] + distance > max_width - 1:
                    distance -= self.step
                    break
                elif (img[top_xy[1], top_xy[0]+distance] == color).all():
                    distance += self.step
                else:
                    distance -= self.step
                    break
            topright_xy = (top_xy[0]+distance, top_xy[1])

            # Move downward to find bottom right coordinate
            distance = 0
            while True:
                if topright_xy[1] + distance > max_height - 1:
                    distance -= self.step
                    break
                elif (img[topright_xy[1]+distance, topright_xy[0]] == color).all():
                    distance += self.step
                else:
                    distance -= self.step
                    break
            bottomright_xy = (topright_xy[0], topright_xy[1]+distance)

            text_boxes.append([topleft_xy, bottomright_xy])

        return text_boxes

    def get_text_groups(self, img, texts, coordinates, text_boxes):
        max_height, max_width = img.shape[:2]
        
        text_groups = []
        for box in text_boxes:
            text_groups.append([])
        
        for i in range(len(texts)):
            tl = coordinates[i][0]

            # Find the corresponding box of the text
            for j in range(len(text_boxes)):
                top = text_boxes[j][0][1]
                bottom = text_boxes[j][1][1]
                left = text_boxes[j][0][0]
                right = text_boxes[j][1][0]
                if left < tl[0] < right and top < tl[1] < bottom:
                    text_groups[j].append(texts[i])
                    break
        
        for i in range(len(text_boxes)):
            if text_boxes[i][1][0] - text_boxes[i][0][0] > max_width * 0.8:
                sentence = " ".join(text_groups[i])
                text_groups[i] = [sentence]
            else:
                sentence = "，".join(text_groups[i])
                text_groups[i] = [sentence]

        return text_groups

    def extract_text(self, img):
        result = self.reader.readtext(img)

        texts = []    # Extracted text list separated by newline
        coordinates = []

        for (bbox, text, prob) in result:
            if prob <= 0.1:
                continue    # Skip text with high uncertainty
            
            (tl, tr, br, bl) = bbox

            tl = (int(tl[0]), int(tl[1])) # Top left xy
            br = (int(br[0]), int(br[1])) # Bottom right xy

            texts.append(text)
            coordinates.append([tl, br])

        return texts, coordinates

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
        if texts:
            for i in range(len(texts)):
                img = self.overlay_translated_text(img, texts[i], coordinates[i])
        
        if text_boxes:
            for box in text_boxes:
                cv2.rectangle(img, box[0], box[1], (0, 255, 0), -1)

        h, w = img.shape[:2]
        resize_height = int(h * (self.resize_width / w))
        resize_img = cv2.resize(img, (self.resize_width, resize_height), interpolation=cv2.INTER_AREA)
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

        image_processor = ImageProcessor("ja")

        texts, coordinates = image_processor.extract_text(image)

        print(len(texts))
        print(texts)

        print(len(coordinates))
        print(coordinates)

        text_boxes = image_processor.get_text_box(image, texts, coordinates)
        print("text_boxes")
        print(text_boxes)

        text_groups = image_processor.get_text_groups(image, texts, coordinates, text_boxes)
        print("text_groups")
        print(text_groups)

        image_processor.show_image(image, text_boxes=text_boxes)