import gettext


# Translations
def translate(domain='', localedir='', languages=['it']):
    # def f(x): return x
    try:
        lang = gettext.translation(
            domain, localedir=localedir, languages=languages)
    except FileNotFoundError:
        # print(f'No translation found: {e}')
        lang = gettext.NullTranslations(fp=None)
    finally:
        lang.install()
        f = lang.gettext
    return f
