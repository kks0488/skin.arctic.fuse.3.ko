"""Small deterministic composer for the remote-control search keypad."""
CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
JONG = ' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'
VOWELS = {'ㅗㅏ':'ㅘ','ㅗㅐ':'ㅙ','ㅗㅣ':'ㅚ','ㅜㅓ':'ㅝ','ㅜㅔ':'ㅞ','ㅜㅣ':'ㅟ','ㅡㅣ':'ㅢ'}
FINALS = {'ㄱㅅ':'ㄳ','ㄴㅈ':'ㄵ','ㄴㅎ':'ㄶ','ㄹㄱ':'ㄺ','ㄹㅁ':'ㄻ','ㄹㅂ':'ㄼ','ㄹㅅ':'ㄽ','ㄹㅌ':'ㄾ','ㄹㅍ':'ㄿ','ㄹㅎ':'ㅀ','ㅂㅅ':'ㅄ'}


def compose(raw):
    out = []; i = 0
    while i < len(raw):
        if raw[i] not in CHO or i + 1 >= len(raw) or raw[i+1] not in JUNG:
            out.append(raw[i]); i += 1; continue
        first = raw[i]; vowel = raw[i+1]; i += 2
        if i < len(raw) and vowel + raw[i] in VOWELS:
            vowel = VOWELS[vowel + raw[i]]; i += 1
        final = ' '
        if i < len(raw) and raw[i] in JONG[1:] and not (i+1 < len(raw) and raw[i+1] in JUNG):
            final = raw[i]; i += 1
            if i < len(raw) and final + raw[i] in FINALS and not (i+1 < len(raw) and raw[i+1] in JUNG):
                final = FINALS[final + raw[i]]; i += 1
        out.append(chr(0xAC00 + (CHO.index(first)*21 + JUNG.index(vowel))*28 + JONG.index(final)))
    return ''.join(out)


def initials(text):
    return ''.join(CHO[(ord(c)-0xAC00)//588] if 0xAC00 <= ord(c) <= 0xD7A3 else c for c in text)
