import gettext


# Translations
def translate(domain='', localedir='', languages=['it']):
    try:
        lang = gettext.translation(
            domain, localedir=localedir, languages=languages)
    except FileNotFoundError:
        lang = gettext.NullTranslations(fp=None)
    finally:
        lang.install()
        f = lang.gettext
    return f
