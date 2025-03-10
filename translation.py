"""
The translator class takes a 2d list of item specifics and translates them into a 3d list containing item specifics that are uploadable to:
USA
UK
Australia
France
Germany
Italy
Spain
"""
from deep_translator import GoogleTranslator

import re
import time
import requests
import functools

import tools


class EbayTranslator:
    TITLE_MAX_LENGTH = 80
    SPAM_EMAIL = "hanzomain901@gmail.com"
    GOOGLE_TRANSLATE_CODES = (None, None, None, "fr", "de", "it", "es")
    DEFAULT_COUNTRY_CODES = ("US", "UK", "AUS", "FR", "DE", "IT", "ES")

    def __init__(self, item_type, upload_mode):
        self.upload_mode = upload_mode
        self.item_type = item_type
        self.translators = (
            GoogleTranslator(source="auto", target="french"),
            GoogleTranslator(source="auto", target="german"),
            GoogleTranslator(source="auto", target="italian"),
            GoogleTranslator(source="auto", target="spanish")
        )
        self.rates = requests.get(
            f"https://api.fastforex.io/fetch-multi?from=USD&to=EUR,AUD,GBP&api_key={item_type.translation_data["fastforex-api-key"]}",
            headers = {"Accept": "application/json"}
        ).json()["results"]
        self.usd_rate = 1 / self.rates["GBP"]

    def translate(self, items):
        """
        Translates a given list of item specifics and returns a 3D list containing the translations
        :param items: 2d_list
        :return: 3d_list
        """
        translated_items = []
        item_count = 0
    
        website_upload = self.upload_mode.upload_state[7]
        general_translation_data = self.item_type.translation_data
        no_long_text_translation = general_translation_data.get("no_long_text_translation")

        for item in items:
            item_count += 1
            print(f"Translating {item_count} / {len(items)}")
            
            item_translation = []

            for i,gt_code in enumerate(self.GOOGLE_TRANSLATE_CODES):
                country_code = general_translation_data["country_codes"][i]
                if (not self.upload_mode.upload_state[i] or not country_code) and ((not website_upload) or i != 1):
                    item_translation.append(None)
                    continue
                
                translation_data = general_translation_data["translation_data"][i] if (general_translation_data["translation_data"]) else None

                if translation_data:
                    country_translation = {}
                    for header,detail in item.items():
                        detail_add = detail
                        if header in translation_data.keys():
                            for key,value in translation_data[header].items():
                                if key == "":
                                    if detail_add == "":
                                        detail_add = value
                                else:
                                    detail_add = re.sub(key, value, detail_add, flags=re.IGNORECASE)

                        if header in general_translation_data["google_translate_fields"]:
                            if (country_code in no_long_text_translation) or (not gt_code) or (not detail_add.strip()):
                                country_translation[header] = detail_add
                                continue

                            for key,value in general_translation_data["condition_translation"][header].items():
                                if detail_add == key:
                                    detail_add = value[i-3]
                                    break
                            else:
                                attempts = 0
                                while attempts < 4:
                                    try:
                                        detail_add = self.translators[i-3].translate_batch([detail])
                                        if not type(detail_add) is str:
                                            detail_add = detail_add[0]
                                        print("GT used")
                                        break
                                    except AttributeError as error:
                                        print(error)

                                    attempts += 1
                                    time.sleep(0.5)
                                    if attempts >= 3:
                                        print("GT Error")

                        country_translation[header] = detail_add

                    if not (country_code in no_long_text_translation):
                        inside_leg = country_translation["IS_Inside Leg"][:2]
                        country_translation["IS_Inside Leg"] = tools.in_to_cm(inside_leg) + "cm"  # Take the first two numbers and convert to cm

                    if gt_code == "it" or (gt_code == "de" and item["IS_Department"] == "Men"):
                        country_translation["IS_Size"] = "W" + country_translation["IS_Size"]

                    concat_condition = []
                    for condition_name in general_translation_data["condition_translation"].keys():
                        condition = country_translation[condition_name]
                        if condition and condition != " ":
                            concat_condition.append(condition)
                    country_translation["eBay Condition Description"] = general_translation_data["condition_openers"][i] + " ••••• ".join(concat_condition)

                    country_translation["Fixed Price eBay"] = self.currency_change(float(country_translation["Fixed Price eBay"]), general_translation_data["currency_codes"][i])
                    country_translation["IS_Department"] = country_translation["IS_Department"].replace("DaHerren", "Damen")
                    country_translation["Title"] = self.title_fix(country_translation, i, country_code)

                else:
                    country_translation = item

                html = self.html_fix(country_translation, i)
                if html != "error":
                    country_translation["eBay Description"] = html
                    item_translation.append(country_translation)
                else:
                    item_translation.append(None)

            translated_items.append(item_translation)
        return translated_items

    def currency_change(self, amount, currency):
        """
        Converts inputted currency
        :param amount: float
        :param cur: string
        :return: string
        """
        if currency == "GBP":
            return str(amount)
        elif currency == "USD":
            return str(round(self.usd_rate * amount, 2))
        else:
            return str(round(self.rates[currency] * amount * self.usd_rate, 2))

    def remove_foreign_dupes(self, word):
        """
        Removes duplicates of a different language
        :param word: string
        :return: string
        """
        final_word = word
        for key,value in self.item_type.translation_data["translation_dupes"].items():
            if key.lower() in final_word.lower():
                for replace in value:
                    final_word = re.sub(" " + replace, "", final_word, flags=re.IGNORECASE)
        return final_word

    def get_val(self, item, country_num, component):
        """
        Recursive function that evaluates values in the title order found in the translation JSON file
        Component is passed as a string beggining with a one character prefix which can be one of:
         &  Returns the item data with the following header name
         $  Returns data based on whether a condition is true or false, arguments are seperated by semicolons,
            Arguments:
              1st: first value
              2nd: operator
              3rd: second value (name of header)
              4th: return value
        If no prefix is specified the string is simply returned

        Operators:
         In - Checks if the second value contains the first value
         Eq - Checks if the first and second values are equal
        """
        if not component:
            return None

        prefix, *data = component
        data = "".join(data)
        if prefix == "&":
            if item[data]:
                return item[data]
        elif prefix == "$":
            first_val, operator, second_val, return_val = data.split(";")
            if operator == "In":
                if first_val in item[second_val]:
                    return self.get_info(return_val)
            elif operator == "Eq":
                if first_val == item[second_val]:
                    return self.get_info(return_val)
                elif first_val in self.trans_data:
                    if "&" in return_val:
                        return self.get_info(return_val)
                    val = self.trans_data[return_val][country_num]
                    return val
        else:
            return component

    def title_fix(self, item, country_num, country_code):
        """
        Creates a title using the translated item specifics
        :param item: 2d_list
        :param country_num: int
        :return: string
        """
        if country_code in self.item_type.translation_data["title_ignore"]:
            return item["Title"]

        self.trans_data = self.item_type.translation_data["title_fixing_data"]
        self.get_info = functools.partial(self.get_val, item, country_num)
        data = self.item_type.translation_data["title_order"]
        title = ""
 
        for component in data:
            returned = self.get_info(component)
            if returned:
                if returned[0] == "#":
                    title = title[:-1]  # Hashtags leave no spaces
                    returned = returned[1:]
                title += returned + " "

        title = tools.remove_dupes(title)
        return self.shorten_title(title, country_num)

    def shorten_title(self, title, country_num):
        if len(title) <= self.TITLE_MAX_LENGTH:
            return title
        trans = self.item_type.translation_data["category_specific_translations"]

        remove = (trans["womens_size"][country_num], " " + trans["blue"][country_num], " WMN", trans["stretch"][country_num], trans["mens"][country_num], trans["womens"][country_num], "end")
        i = 0
        while len(title) > self.TITLE_MAX_LENGTH and i < len(remove):
            title = re.sub(remove[i], "", title, flags=re.IGNORECASE)
            i += 1

        while title[0] == " ":
            title = title[1:]

        return title

    def html_fix(self, item, country_num):
        """
        Creates html using the translated item specifics
        :param self: object
        :param item: 2d_list
        :param country_num: int
        :return: string
        """
        translation_data = self.item_type.translation_data
        if translation_data.get("leave_html"):
            return item["eBay Description"]

        try:
            country_code = self.item_type.translation_data["country_codes"][country_num]
            data = self.item_type.translation_data["html"][country_code]
        except KeyError:
            print(f"HTML or country code for country number {country_num} is missing or incorrect")
            return "error"

        html = ""
        for cell in data:
            if cell[0] == "$":
                temp = cell[1:].split(";")
                html += str(round(float(item[temp[0]]) * float(temp[1])))
            elif "<" in cell:
                html += cell
            else:
                html += item[cell]

        return html
