import fractions
import pickle
import abc
import sys
import math
import dataclasses
from typing import Any, Dict, List, Tuple, Optional
from string import ascii_lowercase as lowers


UNI_A_L = ord('a')
UNI_A_U = ord('A')
UNI_Z_L = ord('z')
UNI_Z_U = ord('Z')


@dataclasses.dataclass
class Cipher:
    text: str = ''

    # смещение символа по mod26 в латинском алфавите
    @staticmethod
    def rotate(key_: int, i: str) -> int:
        if i.islower():
            return (ord(i) - UNI_A_L + key_) % 26 + UNI_A_L
        else:
            return (ord(i) - UNI_A_U + key_) % 26 + UNI_A_U

    # метод для кодирования текста по заданному ключу
    @abc.abstractmethod
    def encode(self, key: str) -> str:
        pass

    # метод для декодирования текста по заданному ключу
    @abc.abstractmethod
    def decode(self, key: str) -> str:
        pass

    # метод, возвращающий в нижнем регистре все буквы алфавита
    # в тексте по порядку
    def get_letters(self) -> str:
        tmp: str = ''
        for i in self.text:
            if UNI_A_L <= ord(i.lower()) <= UNI_Z_L:
                tmp += i.lower()
        return tmp


@dataclasses.dataclass
class Caesar(Cipher):

    def encode(self, key_: str) -> Optional[str]:
        encoded: str = ''
        try:
            key: int = int(key_)
        except ValueError:
            print("For Caesar cipher you should enter a number, try again.")
            sys.exit()
        for i in self.text:
            if UNI_A_L <= ord(i) <= UNI_Z_L or UNI_A_U <= ord(i) <= UNI_Z_U:
                encoded += chr(self.rotate(key, i))
            else:
                encoded += i
        return encoded

    def decode(self, key: str) -> str:
        decoded: str = ''
        try:
            key_: int = int(key)
        except ValueError:
            print("For Caesar cipher you should enter a number, try again.")
            sys.exit()
        decoded = self.encode(str(-key_))
        return decoded

    # метод "обучения" программы (возвращает рез-ты частотного анализа)
    def train(self) -> bytes:
        alphabet: Dict[str, Any] = dict(zip(lowers,
                                            26 * [fractions.Fraction(0, 1)]))
        for i in self.get_letters():
            alphabet[i] += 1
        s: int = sum(alphabet.values())
        if s:
            for i in alphabet.keys():
                alphabet[i] = fractions.Fraction(alphabet[i], s)
        else:
            print("Train text is incorrect: no latin letters.")
            sys.exit()
        return pickle.dumps(alphabet)

    # находит самое правдоподобное смещение алфавита, сравнивая рез-ты
    # частотного анализа у модели и у данного текста
    def similar(self, model: Dict[str, int]) -> int:
        similarity: List[int, int] = [math.inf, 0]  # 1-similarity,2-rotation
        tmp: int = 0
        for i in range(26):
            frequency = pickle.loads(Caesar(self.encode(str(i))).train())
            for j in lowers:
                tmp += abs(model[j] - frequency[j])
            if similarity[0] > tmp:
                similarity = [tmp, i]
            tmp = 0
        return similarity[1]

    # "взлом" шифра Цезаря
    def hack(self, model: Dict[str, int]) -> str:
        return self.encode(str(self.similar(model)))


@dataclasses.dataclass
class Vigenere(Cipher):

    def encode(self, key: str) -> str:
        encoded: str = ''
        if key.isalpha():
            key_length: int = len(key)
            index: int = 0
            for i in self.text:
                if UNI_A_L <= ord(i) <= UNI_Z_L or UNI_A_U <= ord(i) <= UNI_Z_U:
                    key_index: int = ord(key[index].lower()) - UNI_A_L
                    encoded += chr(self.rotate(key_index, i))
                    index = (index + 1) % key_length
                else:
                    encoded += i
        else:
            print("You must enter a word, consisting of latin letters only.")
            sys.exit()
        return encoded

    def decode(self, key: str) -> str:
        new_key: str = ''
        if key.isalpha():
            for i in key:
                new_key += chr((UNI_A_L - ord(i.lower())) % 26 + UNI_A_L)
        return self.encode(new_key)

    # принимает строку letters только с символами из латинского алфавита в
    # нижнем регистре, возвращая слова длиной с предполагаемую длину ключа t
    @staticmethod
    def split_text(letters: str, t: int) -> List[str]:
        words: List[str] = []
        tmp: str = ''
        for i in letters:
            tmp += i
            if len(tmp) == t:
                words.append(tmp)
                tmp = ''
        if tmp:
            words.append(tmp)
        return words

    # считает индекс совпадений в данном тексте
    def index_eval(self, letters: str, t: int) -> Tuple[fractions.Fraction,
                                                        List[str]]:
        words: List[str] = self.split_text(letters, t)
        critical: int = len(words[-1])
        str_len: int = len(words)
        diff: int = 0
        average: fractions.Fraction = fractions.Fraction(0, 1)
        for i in range(t):
            if i >= critical and str_len != 1:
                diff = -1
            for j in lowers:
                index_j: int = 0
                for k in range(len(words)):
                    if k != (len(words) - 1) or diff != -1:
                        index_j += (words[k][i] == j)
                average += fractions.Fraction(index_j * (index_j - 1),
                                              (str_len + diff) *
                                              (str_len + diff - 1))
        average /= t
        return average, words

    # считает взаимный индекс совпадений двух строк
    @staticmethod
    def m_index_eval(encoded: str, guesser: str) -> fractions.Fraction:
        l1: int = len(encoded)
        l2: int = len(guesser)
        m_index: fractions.Fraction = fractions.Fraction(0, 1)
        for i in lowers:
            count_1: int = 0
            count_2: int = 0
            for j in encoded:
                if j == i:
                    count_1 += 1
            for j in guesser:
                if j == i:
                    count_2 += 1
            m_index += fractions.Fraction(count_1 * count_2, l1 * l2)
        return m_index

    # возвращает первую правдоподобную длину ключа
    def length(self) -> List:
        en_id: float = 0.06
        en_growth: float = 0.005
        max_: fractions.Fraction = fractions.Fraction(0, 1)
        letters: str = self.get_letters()
        if letters:
            for t in range(2, len(letters) // 2):
                k: Tuple[fractions.Fraction, List[str]] = \
                    self.index_eval(letters, t)
                if (k[0] - max_) > en_growth and k[0] >= en_id:
                    return k[1]
                max_ = max(k[0], max_)
        else:
            print("No latin alphabet symbols to decode.")
        return []

    # возвращает список из разностей между индексами букв ключа в алфавите
    def guess_key(self) -> List[int]:
        en_id: float = 0.055
        key_rots: List[int] = []
        words: List[str] = self.length()
        if words:
            critical: int = len(words[-1])
            key_len: int = len(words[0])
            str_len: int = len(words)
            row1: str = ''.join([words[k][0] for k in range(str_len)])
            for i in range(1, key_len):
                row2: str = ''.join([words[k][i] for k in range(str_len)
                                     if k != str_len - 1 or i < critical])
                for j in range(26):
                    tmp: str = Caesar(row2).encode(str(j))
                    if self.m_index_eval(row1, tmp) > en_id:
                        key_rots.append(26 - j)
                row1 = row2
        return key_rots

    # "взламывает" шифр Виженера, просит выбрать один из 26 взможных
    # наиболее вероятных ключей
    def hack(self) -> str:
        decoded: str = ''
        key_rots: List[int] = self.guess_key()
        if key_rots:
            print("What key do you prefer?")
            possible_keys: List[str] = []
            for i in range(26):
                key: str = chr(UNI_A_L + i)
                for j in key_rots:
                    key += chr((ord(key[-1]) - ord('a') + j) % 26 + ord('a'))
                possible_keys.append(key)
                print(f"{i + 1}) {key};")
            decoded = self.decode(possible_keys[int(input()) - 1])
        if not decoded:
            print("The text is inappropriate for hacking. Or it's decoded.")
        return decoded


@dataclasses.dataclass
class Vernam(Cipher):

    def encode(self, key: str) -> str:
        encoded: str = ''
        if set(key.lower()).issubset(set(line)):
            key_id: int = 0
            key_length: int = len(key)
            for i in self.text:
                if i.lower() in line:
                    locked: int = vernam_code[i.lower()] ^ vernam_code[
                        key[key_id]]
                    encoded += line[locked]
                    key_id = (key_id + 1) % key_length
                else:
                    encoded += i
        else:
            print("Inappropriate key.",
                  "It has to consist of latin letters or ? !:,.")
        return encoded

    def decode(self, key: str) -> str:
        return self.encode(key)


ciphers = {'caesar': Caesar, 'vigenere': Vigenere, 'vernam': Vernam}
line = ' abcdefghijklmnopqrstuvwxyz.,:!?'
vernam_code = dict(zip(line, range(len(line))))
