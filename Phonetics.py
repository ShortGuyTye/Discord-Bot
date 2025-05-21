import re

def phonetic(message, phonetics, soundList):
    message = message.upper()
    newWords = []
    words = re.findall("[a-zA-Z0-9']+|\\W+", message)
    for ele in words: #loop through each word in message
        new_word = ""
        if phonetics.get(ele) == None:
            new_word += ele.lower()
        else:
            sounds = phonetics.get(ele)
            for sound in sounds:
                new_word += soundList.get(sound)

        newWords.append(new_word)
    final = ""
    for ele in newWords: #reconstruct the word
        final += ele
    return final

def wordDict(phonetics):
    file = open("/Users/mtmcr/Documents/Python/Phonetic-Discord-Bot/Dictionary.txt", "r")
    for line in file:
        sounds = re.findall("\\S+", line)
        key = sounds[0]
        sounds.pop(0)
        phonetics.update({key: sounds})
    return phonetics

def soundDict(soundList):
    soundList.update({"AA": "ah"})
    soundList.update({"AE": "a"})
    soundList.update({"AH": "uh"})
    soundList.update({"AO": "aw"})
    soundList.update({"AW": "ow"})
    soundList.update({"AX": "uh"})
    soundList.update({"AY": "i"})
    soundList.update({"EH": "e"})
    soundList.update({"ER": "er"})
    soundList.update({"EY": "ay"})
    soundList.update({"IH": "ih"})
    soundList.update({"IY": "ee"})
    soundList.update({"OW": "oh"})
    soundList.update({"OY": "oy"})
    soundList.update({"UH": "oo"})
    soundList.update({"UW": "ew"})
    soundList.update({"B": "b"})
    soundList.update({"CH": "ch"})
    soundList.update({"D": "d"})
    soundList.update({"DH": "dth"})
    soundList.update({"DX": "dd"})
    soundList.update({"EL": "el"})
    soundList.update({"EM": "em"})
    soundList.update({"EN": "en"})
    soundList.update({"F": "f"})
    soundList.update({"G": "g"})
    soundList.update({"HH": "h"})
    soundList.update({"JH": "j"})
    soundList.update({"K": "k"})
    soundList.update({"L": "l"})
    soundList.update({"M": "m"})
    soundList.update({"N": "n"})
    soundList.update({"NG": "ng"})
    soundList.update({"P": "p"})
    soundList.update({"Q": "uh"})
    soundList.update({"R": "r"})
    soundList.update({"S": "s"})
    soundList.update({"SH": "sh"})
    soundList.update({"T": "t"})
    soundList.update({"TH": "th"})
    soundList.update({"V": "v"})
    soundList.update({"W": "w"})
    soundList.update({"WH": "w"})
    soundList.update({"Y": "y"})
    soundList.update({"Z": "z"})
    soundList.update({"ZH": "zh"})
    return soundList