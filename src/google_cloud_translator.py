import os
import sys
import time
from google.cloud import translate_v3

class GoogleCloudTranslator:

    def __init__(self, project_id):
        self.project_id = project_id
        self.client = translate_v3.TranslationServiceClient()
        self.parent = f"projects/{self.project_id}/locations/global"

        # MIME type of the content to translate.
        # Supported MIME types:
        # https://cloud.google.com/translate/docs/supported-formats
        self.mime_type = "text/plain"

    def translate(self, source_language_code, target_language_code, text):
        # Translate text from the source to the target language.
        response = self.client.translate_text(
            contents=text,
            parent=self.parent,
            mime_type=self.mime_type,
            source_language_code=source_language_code,
            target_language_code=target_language_code,
        )

        # Display the translation for the text.
        # For example, for "Hello! How are you doing today?":
        # Translated text: Bonjour comment vas-tu aujourd'hui?
        #for translation in response.translations:
            #print(f"Translated text: {translation.translated_text}")

        return response.translations


if __name__ == "__main__":
    # Set the environment variable for authentication.
    #os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/credentials.json"

    try:
        with open('project_id.txt', 'r') as file:
            PROJECT_ID = file.read()
    except:
        print("Error: project_id.txt not found or unreadable.")
        sys.exit(1)

    start_time = time.perf_counter()
    if len(sys.argv) == 2:
        if sys.argv[1] == "debug":
            translator = GoogleCloudTranslator(PROJECT_ID)
            # The text to translate.
            texts = ["おはよう", "こんにちは", "こんばんは", "ありがとう", "さようなら", "すみません", "ごめんなさい"]

            translator.translate("ja", "zh-TW", texts)
        else:
            translator = GoogleCloudTranslator(PROJECT_ID)
            translator.translate("ja", "zh-TW", [sys.argv[1]])

    end_time = time.perf_counter()
    print(f"Execution time: {end_time - start_time:.2f} seconds")