import gettext


# Translations
def translate(domain='', localedir='', languages=['it']):
    def f(x): return x
    try:
        lang = gettext.translation(
            domain, localedir=localedir, languages=languages)
        lang.install()
    except FileNotFoundError as e:
        # print(f'No translation found: {e}')
        lang = gettext.NullTranslations(fp=None)
        lang.install()
    finally:
        f = lang.gettext
    return f