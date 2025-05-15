import argparse
from colorama import Style, init
from cache import get_from_cache, store_to_cache
from entry import Entry, Grammar
from focloir import get_from_focloir


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

    parser.add_argument('-e',
                        '--examples',
                        help='Set flag to disable examples',
                        action='store_true')

    return vars(parser.parse_args())


def get_translation(word: list[str], args: dict) -> list[Entry]:
    translation: list[Entry] = get_from_cache(word)

    if not translation:
        translation = get_from_focloir(word)
        args['cache'] = True
    else:
        args['cache'] = False

    return translation


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
                print(Style.BRIGHT + f'\t{exam.original}', end=' ')
                print(exam.translations)

        print()


def main() -> None:
    args: dict = parse_args()

    query = args.pop('query')
    entries: list[Entry] = get_translation(query, args)

    if args['cache']:
        store_to_cache(query, entries)

    print_translations(entries, **args)


if __name__ == '__main__':
    main()
