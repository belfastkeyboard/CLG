import argparse
from colorama import Style, init
from cache import get_from_cache, store_to_cache
from entry import Entry, Grammar
from focloir import get_from_focloir
from tearma import get_from_tearma
import requests
from requests import Response
from bs4 import BeautifulSoup


def parse_args() -> dict:
    parser = argparse.ArgumentParser(
        description='Command Line Gaeilge, a tool for Irish language translation.\n',
        epilog='Example: python main.py hello',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(dest='query',
                        nargs='+',
                        help='Word or phrase to translate')

    parser.add_argument('-d', '--dictionary',
                        choices=['focloir', 'tearma', 'teanglann'],
                        default='focloir',
                        help='Dictionary to use')

    parser.add_argument('-l',
                        '--limit',
                        help='Limit number of results to return',
                        type=int)

    parser.add_argument('-e',
                        '--examples',
                        help='Set flag to disable examples',
                        action='store_true')

    return vars(parser.parse_args())


def construct_focloir_query(query: list[str]) -> str:
    return '+'.join(query)


def construct_tearma_query(query: list[str]) -> str:
    return ' '.join(query)


def fetch_from_web(query: list[str], site: str) -> list[Entry]:
    h = {
        'focloir': construct_focloir_query,
        'tearma': construct_tearma_query
    }

    query: str = h.get(site)(query)

    g = {
        'focloir': (f'https://www.focloir.ie/en/dictionary/ei/{query}', get_from_focloir),
        'tearma': (f'https://www.tearma.ie/q/{query}', get_from_tearma)
    }

    url, cb = g.get(site)

    response: Response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 '
                                                                  '(Windows NT 10.0; Win64; x64) '
                                                                  'AppleWebKit/537.36 '
                                                                  '(KHTML, like Gecko) '
                                                                  'Chrome/91.0.4472.124 Safari/537.36'})

    if response.status_code != 200:
        response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    return cb(query, soup)


def get_translation(query: list[str], site: str) -> list[Entry]:
    entries: list[Entry] = get_from_cache(query, site)

    if not entries:
        entries = fetch_from_web(query, site)
        store_to_cache(query, entries, site)

    return entries


def print_translations(translations: list[Entry], **kwargs) -> None:
    if not translations:
        return

    init(autoreset=True)

    limit: int = kwargs.get('limit')
    examples: bool = False if kwargs.get('examples') else True

    if limit:
        translations = translations[:limit]

    cat_width: int = max(list(map(lambda s: len(s.grammar.category), translations)))
    dom_width: int = max(list(map(lambda s: len(s.grammar.domain), translations)))
    num_width: int = len(str(len(translations) + 1))

    for i, translation in enumerate(translations):
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

        if examples:
            for exam in translation.examples:
                print(end='\t')
                if exam.original:
                    print(Style.BRIGHT + exam.original, end=' ')
                if exam.translations:
                    print(exam.translations)

        print()


def main() -> None:
    args: dict = parse_args()

    query: list[str] = args.pop('query')
    site: str = args.pop('dictionary')

    entries: list[Entry] = get_translation(query, site)

    print_translations(entries, **args)


if __name__ == '__main__':
    main()
