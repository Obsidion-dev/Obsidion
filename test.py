import re

minecraft = (
    "ᔑ",
    "ʖ",
    "ᓵ",
    "↸",
    "e",
    "⎓",
    "⊣",
    "⍑",
    "╎",
    "⋮",
    "ꖌ",
    "ꖎ",
    "ᒲ",
    "リ",
    "𝙹",
    "!¡",
    "ᑑ",
    "∷",
    "ᓭ",
    "ℸ ̣",
    "⚍",
    "⍊",
    "∴",
    "̇̇/",
    "||",
    "⨅",

)
alphabet = (
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
)

response = "y"


for letter in response:
    if letter == "|":
        pass
    elif letter == "y":
        pass
    elif any(letter in i for i in minecraft):
        letter_replace = alphabet[minecraft.index(letter)]
        response = re.sub(letter, letter_replace, response)
    elif any(letter in i for i in alphabet):
        letter_replace = minecraft[alphabet.index(letter)]
        response = re.sub(letter, letter_replace, response)

response = response.replace("||", "y")
response = response.replace("y", "||")


    

print(response)