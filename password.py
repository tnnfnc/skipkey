import re


def strength(password):
    p = password
    l = len(password)
    n = 0
    if len(p) > 8:
        n += 1
    if len(re.findall('[A-Z]', p)) > round(len(p)*0.35):
        n += 1
    if len(re.findall('[a-z]', p)) > round(len(p)*0.35):
        n += 1
    if len(re.findall('[\d]', p)) > round(len(p)*0.15):
        n += 1
    if len(re.findall('[\W]', p)) > round(len(p)*0.20):
        n += 1
    requirements = n
    # Sum the repeated any type of characters
    n = 0
    r = dict([(c, 0) for c in p])
    for c in p:
        r[c] += 1
    repeated = sum(r.values()) - len(r)

    # Sequentials
    n = 0
    for i in range(1, len(p)):
        d = ord(p[i - 1]) - ord(p[i])
        if d == 1 or d == -1:
            n += 1
    sequentials = n
    # Symbols or numbers not in the first or last position
    # Minimum 8 characters in length Contains 3/4 of the following items:
    # Uppercase Letters - Lowercase Letters - Numbers - Symbols
    good = 4 * len(re.findall('[a-zA-Z]', p)) + \
        2 * (l - len(re.findall('[A-Z]', p))) + \
        2 * (l - len(re.findall('[a-z]', p))) + \
        4 * len(re.findall('\d', p)) + \
        6 * len(re.findall('\W', p)) + \
        2 * len(re.findall('[\d|\W]', p[1:-1])) + \
        2 * requirements

    bad = len(re.findall('[a-zA-Z]', p)) + \
        len(re.findall('\d', p)) + \
        repeated + \
        2 * len(re.findall('[A-Z]{2,}', p)) + \
        2 * len(re.findall('[a-z]{2,}', p)) + \
        2 * len(re.findall('\d{2,}', p)) + \
        3 * sequentials
    return int(good - bad)


def requirements(text):
    r = dict(letters=round(len(text)*52/89),
             numbers=round(len(text)*10/89),
             symbols=round(len(text)*27/89))
    return r


if __name__ == '__main__':
    print(requirements('fjHKiHykLOOò;:.ò* kd7'))
    print(strength('fjHKiHykLOOò;:.ò* kd7'))
    print(strength(''))
    print(strength(' '))
