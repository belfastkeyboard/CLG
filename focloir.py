from bs4 import BeautifulSoup, ResultSet, Tag
from entry import Entry, Example, Grammar, Translation
import requests
from requests import Response


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


def parse_focloir_response(word: str, entry: Tag) -> list[Entry]:
    results: list[Tag] = list(entry.find_all('span', class_='sense'))
    results = list(filter(lambda s: s.find('span', class_='span_sensenum') and s.find('span', class_='pos'), results))

    translations = []

    for result in results:
        quotes: list[Translation] = parse_focloir_translations(result)
        grammar = parse_focloir_grammar(result)
        examples = parse_focloir_examples(result)

        translations.append(Entry(word, grammar, quotes, examples))

    return translations


def get_from_focloir(word: list[str]) -> list[Entry]:
    query: str = '+'.join(word)

    url: str = f'https://www.focloir.ie/en/dictionary/ei/{query}'

    response: Response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 '
                                                                  '(Windows NT 10.0; Win64; x64) '
                                                                  'AppleWebKit/537.36 '
                                                                  '(KHTML, like Gecko) '
                                                                  'Chrome/91.0.4472.124 Safari/537.36'})

    if response.status_code != 200:
        response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    entry: Tag = soup.find('div', class_='entry')

    return parse_focloir_response(query, entry) if entry else []
