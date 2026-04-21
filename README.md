# game-screen-text-translator

## Overview
`image_text_translator.py` is the script for extracting text from an image or live game screen using EasyOCR(an open source project of Jaided AI), translating it into other language.

I make it for Switch 2 Pokemon FireRed Japanese version. It has a clear text box which makes it easier to detect the related text region. Also, [fine-tune of the OCR](#ocr-model-training) model is required in order improve the text extraction accuracy.

### Demo
![](img/demo.jpg)

## Function flow
1. Initialize the OCR and translator objects:
   - `image_processor = ImageProcessor("ja"), recog_network)`
   - `translator = Translator("ja", "zh-TW")`
2. `translate_text_on_image(img, image_processor, translator)` does the main work:
   - Extract text and coordinates from the image using `image_processor.extract_text()`.
   - Skip translation if the detected text is identical to the previous frame.
   - Create text bounding boxes with `image_processor.get_text_box()`.
   - Group related detected text regions with `image_processor.get_text_groups()`.
   - For each text group, print the original text and translated text.
3. Command-line behavior:
   - If a single argument is provided and it is a file, the script reads the image and translates it.
   - If a single argument is provided and it is a directory, the script processes each image file in the folder.
   - If no argument is provided, the script starts a live capture session for the configured game window.

## Usage
### 1) Translate a single image file
```powershell
python image_text_translator.py path\to\image.png
```

### 2) Translate all images in a folder
```powershell
python image_text_translator.py path\to\image_folder
```

- The script will pause and wait for `Enter` after each image in the folder.

### 3) Run live capture translation
```powershell
python image_text_translator.py
```

- This mode uses `WindowsCapture` to grab the game window defined by `window_title`.
- By default the script uses `Projector - Source: GC573`.
- Change `window_title` in the script if your capture window has a different name.

## Important notes
- The live capture mode crops the left and right edges of the frame before OCR.
- If you change capture hardware or OBS settings, update the `window_title` value accordingly.

## OCR Model Training
The OCR result did't look good when I used japanese_g2.pth model downloaded from https://www.jaided.ai/easyocr/modelhub/. It is expected because the pre-trained model may not be trained with the font that used in this kind of old Pokemon game.![](img/map_1.jpg)

I included the trainer program from EasyOCR https://github.com/JaidedAI/EasyOCR and made some modifications on it. I trained the japanese_g2.pth model with Pokemon japanese text image and the result looks much better.

### Steps
1. Prepare all training data images in easyocr_trainer/all_data/[folder name defined in select_data of config.yaml] and images, labels.csv in all_data/validation. Data in validation folder is used to test the fine-tuned model.

    For example:

    #### 1.jpg
    ![1.jpg](img/1.jpg)
    #### 2.jpg
    ![2.jpg](img/2.jpg)

2. Create labels.csv in easyocr_trainer/all_data/[folder name defined in select_data of config.yaml] which stores the image file name and the corresponding text on that image.
    #### labels.csv
    ```
    filename,words
    1.jpg,かがくの
    2.jpg,ちからって
    ```

3. Prepare images, labels.csv in easyocr_trainer/all_data/validation for testing the fine-tuned model.

4. Define the file path of the model that you want to fine tune in **saved_model** of config.yml.

5. Run easyocr_trainer/trainer.py
    ```
    python trainer.py
    ```

6. Copy the fine-tuned model in easyocr_trainer/saved_models to ~/.EasyOCR/model. I would use best_accuracy.pth in that folder.

7. Copy the yaml and python file in custom_model to ~/.EasyOCR/model/user_network. Ensure the name of all these two files and the pth file in model folder are the same. Moreover, you may need to change the values in the yaml file.

8. Update `recog_network` in image_text_translator.py to the name of your custom model.

## Google cloud translator
### Setup
Refer to https://docs.cloud.google.com/translate/docs/setup for detailed steps.
1. Create project in Google Cloud, take note of the project ID
2. Enable Billing
3. Enable Cloud Translation API
4. Install and init gcloud CLI
5. Create Application default credentials in gcloud CLI by running `gcloud auth application-default login`