"""Shared standardisation function"""


from re import sub

from unidecode import unidecode


def standardise(string):
    """Standardise a place/street name string to allow comparison

    N.B. different from fhodot.app.suggest.standardise_name function,
    which is intended for standardising establishment names for improved
    fuzzy matching
    """
    string = unidecode(string) # unaccent
    string = string.lower()
    # convert various characters to something specific
    string = sub("[./-]", " ", string)
    string = sub(r" ?& ?| ?\+ ?", " and ", string)
    # remove any extraneous characters
    string = sub(r"[^a-z\s]", "", string)
    # normalise whitespace
    string = string.strip()
    string = sub(r"\s+", " ", string)
    return string
