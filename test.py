class Father:
    name = "아버지"

    def getLicense(self):
        return "driver's lic."
    def getAlcohol(self):
        return "beer"

class Son(Father):
    name = "아들"
    # def getLicense(self):
    #     return "none"
    def getAlcohol(self):
        return "soju"


f = Father()
print(f.getLicense())

s = Son()
print(s.getLicense())
print(s.getAlcohol())

print()
print()







'''
class hello:
    t = '내가 상속해 줬어'

    @classmethod
    def calc(cls):
        return cls.t

class hello_2(hello):
    t = '나는 상속 받았어'

print(hello_2.calc())


class Language:
    default_language = "English"

    def __init__(self):
        self.show = '나의 언어는' + self.default_language

    @classmethod
    def class_my_language(cls):
        return cls()

    @staticmethod
    def static_my_language():
        return Language()

    def print_language(self):
        print(self.show)


class KoreanLanguage(Language):
    default_language = "한국어"


a = KoreanLanguage.static_my_language()
b = KoreanLanguage.class_my_language()
a.print_language()
b.print_language()

'''