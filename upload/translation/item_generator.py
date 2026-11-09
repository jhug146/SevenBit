import re
import html as html_lib
import requests
import functools

from upload.models.item import Item


def _in_to_cm(value):
    return str(round(int(value) * 2.5))


def _remove_dupes(word, repeat=True):
    word_list = word.split(" ")
    dupe_list = []
    final_list = []
    for word in word_list:
        if not (word.lower() in dupe_list) and word:
            final_list.append(word)
            dupe_list.append(word.lower())
    if repeat:
        return _remove_dupes(" ".join(final_list), False)
    return " ".join(final_list)


class ItemGenerator:
    TITLE_MAX_LENGTH = 80
    SUMMARY_MAX_LENGTH = 800

    def __init__(self, translation_config, accounts):
        self.translation_config = translation_config
        self.accounts = accounts
        self.rates = requests.get(
            f"https://api.fastforex.io/fetch-multi?from=USD&to=EUR,AUD,GBP&api_key={accounts.fastforex_api_key}",
            headers={"Accept": "application/json"}
        ).json()["results"]
        self.usd_rate = 1 / self.rates["GBP"]

    def generate(self, translated_dict, country_index, gt_code, original_item):
        country_code = self.translation_config.country_codes[country_index]
        no_long_text_translation = self.translation_config.no_long_text_translation

        if not (country_code in no_long_text_translation) and country_code != "DE":
            inside_leg = translated_dict["IS_Inside Leg"][:2]
            translated_dict["IS_Inside Leg"] = _in_to_cm(inside_leg) + "cm"

        translated_dict["Price"] = self._currency_change(
            float(translated_dict["Price"]),
            self.translation_config.currency_codes[country_index]
        )
        translated_dict["IS_Department"] = translated_dict["IS_Department"].replace("DaHerren", "Damen")
        translated_dict["Title"] = self._title_fix(translated_dict, country_index, country_code)

        html = self._html_fix(translated_dict, country_index)
        if html == "error":
            return None
        translated_dict["eBay Description"] = html

        result = Item.from_dict(translated_dict)
        if self.accounts.build_condition:
            opener = self.translation_config.condition_openers[country_index]
            parts = [c for c in result.conditions if c and c != " "]
            result.condition_description = opener + " ••••• ".join(parts)

        return result

    def _currency_change(self, amount, currency):
        if currency == "GBP":
            return str(amount)
        elif currency == "USD":
            return str(round(self.usd_rate * amount, 2))
        else:
            return str(round(self.rates[currency] * amount * self.usd_rate, 2))

    def _get_val(self, item, country_num, component):
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
                    if return_val in self.trans_data:
                        return self.trans_data[return_val][country_num]
                    return self.get_info(return_val)
                elif first_val in self.trans_data:
                    if "&" in return_val:
                        return self.get_info(return_val)
                    return self.trans_data[return_val][country_num]
        else:
            return component

    def _title_fix(self, item, country_num, country_code):
        if country_code in self.translation_config.title_ignore:
            return item["Title"]

        self.trans_data = self.translation_config.title_fixing_data
        self.get_info = functools.partial(self._get_val, item, country_num)
        title = ""

        for component in self.translation_config.title_order:
            returned = self.get_info(component)
            if returned:
                if returned[0] == "#":
                    title = title[:-1]
                    returned = returned[1:]
                title += returned + " "

        title = _remove_dupes(title)
        return self._shorten_title(title, country_num)

    def _shorten_title(self, title, country_num):
        if len(title) <= self.TITLE_MAX_LENGTH:
            return title
        trans = self.translation_config.category_specific_translations
        remove = (
            trans["womens_size"][country_num],
            " " + trans["blue"][country_num],
            " WMN",
            trans["stretch"][country_num],
            trans["mens"][country_num],
            trans["womens"][country_num],
            "end"
        )
        i = 0
        while len(title) > self.TITLE_MAX_LENGTH and i < len(remove):
            title = re.sub(remove[i], "", title, flags=re.IGNORECASE)
            i += 1
        while title[0] == " ":
            title = title[1:]
        return title

    def _html_fix(self, item, country_num):
        if self.translation_config.leave_html:
            return item["eBay Description"]

        try:
            country_code = self.translation_config.country_codes[country_num]
            data = self.translation_config.html[country_code]
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

        summary = self._build_summary(item, country_num)
        if summary and html.startswith("<div>"):
            html = "<div>" + summary + html[len("<div>"):]

        return html

    def _build_summary(self, item, country_num):
        # schema.org description block: eBay copies its text into the listing's
        # meta description, which the eBay app shows as the description preview.
        templates = self.translation_config.description_summary
        if not templates or country_num >= len(templates) or not templates[country_num]:
            return ""

        conditions = []
        for key in ("Condition 1", "Condition 2", "Condition 3"):
            text = str(item.get(key) or "").strip()
            if text:
                conditions.append(text if text[-1] in ".!?" else text + ".")

        def lookup(match):
            key = match.group(1)
            if key == "Conditions":
                return " ".join(conditions)
            if key.startswith("$"):
                field, factor = key[1:].split(";")
                try:
                    return str(round(float(item[field]) * float(factor)))
                except (KeyError, ValueError, TypeError):
                    return ""
            return str(item.get(key) or "").strip()

        text = re.sub(r"\{([^{}]+)\}", lookup, templates[country_num])
        text = " ".join(text.split())[:self.SUMMARY_MAX_LENGTH]
        return ('<div vocab="https://schema.org/" typeof="Product">'
                f'<span property="description">{html_lib.escape(text)}</span></div>')
