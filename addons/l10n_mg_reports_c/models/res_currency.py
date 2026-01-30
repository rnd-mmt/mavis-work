from odoo import models
import logging
import math
import re
import time

from odoo import tools

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None

class Currency(models.Model):
    _inherit = "res.currency"
    _description = "Currency"

    #def amount_to_text(self, amount):
    #    amt_word = self.currency_unit_label
    #    return str.title(self._trad(amount)) + " " + amt_word
    def amount_to_text(self, amount):
        self.ensure_one()
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(self.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)

        lang = tools.get_lang(self.env)
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
                        amt_value=_num2words(integer_value, lang=lang.iso_code),
                        amt_word=self.currency_unit_label,
                        )
        if not self.is_zero(amount - integer_value):
            amount_words += ' ' + tools.ustr(' {amt_value}').format(
                        amt_value=_num2words(fractional_value, lang=lang.iso_code),
                       # amt_word=self.currency_subunit_label,
                        )
        # Begin : Ajout d'un 's' à "million" et "milliard" si le nombre précédent est supérieur à 1
        amount_words_lower = str(amount_words).lower()
        words = amount_words_lower.split()
        if "million" in words and words[words.index("million") - 1] != "un":
            amount_words_lower = amount_words_lower.replace(" million", " millions")
        if "milliard" in words and words[words.index("milliard") - 1] != "un":
            amount_words_lower = amount_words_lower.replace(" milliard", " milliards")
        return amount_words_lower
        # End

    def _tradd(self, num):
        global t1, t2
        ch = ''
        if num == 0:
            ch = ''
        elif num < 20:
            ch = t1[num]
        elif num >= 20:
            if (num >= 70 and num <= 79) or (num >= 90):
                z = int(num / 10) - 1
            else:
                z = int(num / 10)
            ch = t2[z]
            num = num - z * 10
            if (num == 1 or num == 11) and z < 8:
                ch = ch + ' et'
            if num > 0:
                ch = ch + ' ' + self._tradd(num)
            else:
                ch = ch + self._tradd(num)
        return ch

    def _tradn(self, num):
        global t1, t2
        ch = ''
        flagcent = False
        if num >= 1000000000:
            z = int(num / 1000000000)
            ch = ch + self._tradn(z) + ' milliard'
            if z > 1:
                ch = ch + 's'
            num = num - z * 1000000000
        if num >= 1000000:
            z = int(num / 1000000)
            ch = ch + self._tradn(z) + ' million'
            if z > 1:
                ch = ch + 's'
            num = num - z * 1000000
        if num >= 1000:
            if num >= 100000:
                z = int(num / 100000)
                if z > 1:
                    ch = ch + ' ' + self._tradd(z)
                ch = ch + ' cent'
                flagcent = True
                num = num - z * 100000
                if int(num / 1000) == 0 and z > 1:
                    ch = ch + 's'
            if num >= 1000:
                z = int(num / 1000)
                if (z == 1 and flagcent) or z > 1:
                    ch = ch + ' ' + self._tradd(z)
                num = num - z * 1000
            ch = ch + ' mille'
        if num >= 100:
            z = int(num / 100)
            if z > 1:
                ch = ch + ' ' + self._tradd(z)
            ch = ch + " cent"
            num = num - z * 100
            if num == 0 and z > 1:
                ch = ch + 's'
        if num > 0:
            ch = ch + " " + self._tradd(num)
        return ch

    def _trad(self, nb, unite="", decim=""):  # ADD decim with vlue: centime if needed
        global t1, t2
        nb = round(nb, 2)
        t1 = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze",
              "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
        t2 = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt",
              "quatre-vingt dix"]
        z1 = int(nb)
        z3 = (nb - z1) * 100
        z2 = int(round(z3, 0))
        if z1 == 0:
            ch = u"zéro"
        else:
            ch = self._tradn(abs(z1))
        if z1 > 1 or z1 < -1:
            if unite != '':
                # ch=ch+" "+unite+'s'
                ch = ch + " " + unite
        else:
            ch = ch + " " + unite
        if z2 > 0:
            ch = ch + " "  # ch=ch+" et "
            ch = ch + self._tradn(z2)

            if z2 > 1 or z2 < -1:
                if decim != '':
                    ch = ch + " " + decim + 's'
            else:
                ch = ch + " " + decim
        if nb < 0:
            ch = "moins " + ch

        return ch
