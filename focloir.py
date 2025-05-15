from bs4 import BeautifulSoup, ResultSet, Tag
from entry import Entry, Example, Grammar, Translation


def parse_focloir_translations(result: Tag) -> list[Translation]:
    cit_translations: ResultSet = result.find_all('span', class_='cit_translation')

    translations: list[Translation] = []

    for t in cit_translations:
        quote: Tag = t.find('span', class_='quote')
        category: Tag = t.find('span', class_='lbl_purple_i')
        grammar: Tag = t.find('span', class_='lbl_black_i')

        quote: str = quote.text.strip()
        category: str = category.text.strip() if category else ''
        grammar: str = grammar.text.strip() if grammar else ''

        translations.append(Translation(quote, category, grammar))

    return translations


def parse_focloir_grammar(result: Tag) -> Grammar:
    category: str = result.find('span', class_='pos').text.strip()
    meaning: str = result.find('span', class_='EDMEANING').text.strip()
    domain = str(''.join(list(map(lambda d: d.text.strip(), result.find_all('span', class_='lbl_purple_sc_i')))))

    return Grammar(category, domain, meaning)


def parse_focloir_examples(result: Tag) -> list[Example]:
    cit_examples: ResultSet = result.find_all('span', class_='cit_example')

    examples: list[Example] = []

    for example in cit_examples:
        quote: str = example.find('span', class_='quote').text.strip()

        translations: str = ''.join(
            map(lambda s: s.text.strip(), example.find_all('span', class_='cit_translation_noline'))
        )

        examples.append(Example(quote, translations))

    return examples


def get_from_focloir(word: str, soup: BeautifulSoup) -> list[Entry]:
    entry: Tag = soup.find('div', class_='entry')

    if not entry:
        return []

    results: list[Tag] = list(entry.find_all('span', class_='sense'))
    results = list(filter(lambda s: s.find('span', class_='span_sensenum') and s.find('span', class_='pos'), results))

    translations = []

    for result in results:
        quotes: list[Translation] = parse_focloir_translations(result)
        grammar = parse_focloir_grammar(result)
        examples = parse_focloir_examples(result)

        translations.append(Entry(word, grammar, quotes, examples))

    return translations
