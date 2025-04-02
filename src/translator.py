import json
import os


class Translator:
    """
    A class to handle translation of text based on locale.

    Attributes:
    locale (str): The locale for the translations.
    translations (dict): The dictionary containing translations.
    current_language (str): The current language being used for translations.
    """

    def __init__(self, locale=None, file_path=None):
        """
        Initializes the Translator with a specified locale and loads translations.

        Args:
        locale (str): The locale for the translations.
        file_path (str): The path to the translation file.
        """
        self.locale = locale
        self.load_translations(file_path)

    def load_translations(self, file_path=None):
        """
        Loads translations from a specified file path.

        Args:
        file_path (str): The path to the translation file.
        """
        if file_path is None:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, 'locales', f'{self.locale}.json')
        with open(file_path, 'r', encoding='utf-8') as file:
            self.translations = json.load(file)
        self.locale = file_path
        self.current_language = self.translate(self.translate("current_language"))

    def translate(self, key):
        """
        Translates a given key based on the loaded translations.

        Args:
        key (str): The key to be translated.

        Returns:
        str: The translated text.
        """
        return self.translations.get(key, key)
