import csv
import sys
from deep_translator import GoogleTranslator

class Translator:

    def __init__(self, source_language, target_language):
        print("Init Translator")
        self.translator = GoogleTranslator(source=source_language, target=target_language)
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

    def translate(self, text):
        print(text)
        print(self.translate_to_romaji(text))

        try:
            print(self.translator.translate(text))
        except:
            print("Warning: Could not translate")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        translator = Translator("ja", "zh-TW")
        translator.translate(sys.argv[1])
    else:
        print("Usage: python translator.py [Japanese words]")