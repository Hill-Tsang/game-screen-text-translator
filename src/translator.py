import csv
import sys
import time
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor

class Translator:

    def __init__(self):
        print("Init Translator")
        self.romaji = self.load_romaji_csv("romaji.csv")

    def load_romaji_csv(self, file_path):
        romaji = {}
        with open(file_path, mode='r', newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            
            for row in csv_reader:
                romaji[row[0]] = row[1]

        return romaji

    def translate_to_romaji(self, text):
        romaji_text = ""

        consonant = False

        for char in text:
            if char == "っ" or char == "ッ":
                consonant = True
                continue
            
            if char == "は":
                if romaji_text and romaji_text[-1] != " ":
                    roma_char = "wa"
                else:
                    roma_char = self.romaji.get(char)
            else:
                roma_char = self.romaji.get(char)
            
            if roma_char is not None:
                if consonant:
                    romaji_text += self.romaji[char][0]
                    consonant = False
                romaji_text += roma_char
            else:
                romaji_text += char

        return romaji_text

    def translate(self, source_language, target_language, text):
        if source_language == "ja" and target_language == "romaji":
            return self.translate_to_romaji(text)
        
        translator = GoogleTranslator(source=source_language, target=target_language)
        try:
            translated = translator.translate(text)
        except:
            translated = ""
        return translated
    
    def batch_translate(self, source_language, target_language, texts):
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda text: self.translate(source_language, target_language, text), texts))
        return results

if __name__ == "__main__":
    start_time = time.perf_counter()
    
    if len(sys.argv) == 2:
        translator = Translator()
        print(translator.translate("ja", "zh-TW", sys.argv[1]))
    else:
        print("Usage: python translator.py [Japanese words]")
    
    end_time = time.perf_counter()
    print(f"Execution time: {end_time - start_time:.2f} seconds")