import argparse
import requests
from requests import Response
from bs4 import BeautifulSoup, ResultSet, Tag
from colorama import Style, init


class Translation:
    def __init__(self, quote: str, category: str, grammar: str):
        self.quote = quote
        self.category = category
        self.grammar = grammar

    def __repr__(self):
        return f'Translation(quote={self.quote}, category={self.category}, grammar={self.grammar})'

    def __str__(self):
        return ' '.join([self.quote, self.category, self.grammar])


class Example:
    def __init__(self, original: str, translations: str):
        self.original: str = original
        self.translations: str = translations

    def __repr__(self):
        return f'Example(original={self.original}, translations={self.translations})'

    def __str__(self):
        return f'{self.original} {self.translations}'


class Grammar:
    def __init__(self, category: str, domain: str, meaning: str):
        self.category: str = category
        self.domain: str = domain
        self.meaning: str = meaning

    def __repr__(self):
        return f'Grammar(category={self.category}, domain={self.domain}, meaning={self.meaning})'


class Entry:
    def __init__(self, original: str, grammar: Grammar, translations: list[Translation], examples: list[Example]):
        self.original: str = original
        self.grammar: Grammar = grammar
        self.translations: list[Translation] = translations
        self.examples: list[Example] = examples

    def __repr__(self):
        return (f'Translation(original={self.original}, grammar={self.grammar}, translations={self.translations}, '
                f'examples={self.examples})')


def parse_args() -> dict:
    parser = argparse.ArgumentParser(
        description='Gaeilge, a command line tool for Irish language translation.\n',
        epilog='Example: python main.py hello',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(dest='query',
                        help='Word or phrase to translate',
                        nargs='+')

    parser.add_argument('-l',
                        '--limit',
                        help='Limit number of results to return',
                        type=int)

    return vars(parser.parse_args())


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


def get_translation(word: list[str]) -> list[Entry]:
    return get_from_focloir(word)


def print_translations(translations: list[Entry], **kwargs) -> None:
    if not translations:
        return

    init(autoreset=True)

    cat_width: int = max(list(map(lambda s: len(s.grammar.category), translations)))
    dom_width: int = max(list(map(lambda s: len(s.grammar.domain), translations)))
    num_width: int = len(str(len(translations) + 1))

    limit: int = kwargs.get('limit')

    for i, translation in enumerate(translations):
        if limit and i >= limit:
            break

        grammar: Grammar = translation.grammar

        meta: str = ' '.join([f'{i + 1: <{num_width}}',
                              f'{grammar.category.upper(): <{cat_width}}',
                              f'{grammar.domain.upper(): <{dom_width}}'])

        print(Style.BRIGHT + meta, end=' ')

        print(grammar.meaning)

        for trans in translation.translations:
            print(f'\t{trans.quote}', end=' ')
            print(Style.DIM + trans.category, end=' ')
            print(Style.BRIGHT + trans.grammar)

        for exam in translation.examples:
            print(Style.BRIGHT + f'\t{exam.original}', end=' ')
            print(exam.translations)

        print()


def main() -> None:
    args: dict = parse_args()
    query = args.pop('query')
    print_translations(get_translation(query), **args)


if __name__ == '__main__':
    main()
