import argparse
import requests
from requests import Response
from bs4 import BeautifulSoup, ResultSet, Tag
from colorama import Style, init
import sqlite3
from pathlib import Path
import os

CACHE = Path(os.path.dirname(os.path.abspath(__file__)), '.cache', 'storage.db')


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
        return (f'Entry(original={self.original}, grammar={self.grammar}, translations={self.translations}, '
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

    parser.add_argument('-e',
                        '--examples',
                        help='Set flag to disable examples',
                        action='store_true')

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


def get_from_cache(query: list[str]) -> list[Entry]:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    query = ' '.join(query)
    results: list[Entry] = []

    with sqlite3.connect(CACHE) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                time TIMESTAMP                         
        )""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS grammars (
                id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                domain TEXT NOT NULL,
                meaning TEXT NOT NULL
        )""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY,
                quote TEXT NOT NULL,
                category TEXT NOT NULL,
                grammar TEXT NOT NULL
        )""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS examples (
                id INTEGER PRIMARY KEY,
                original TEXT NOT NULL,
                translations TEXT NOT NULL
        )""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS lookup_grammar (
                query_id INTEGER,
                grammar_id INTEGER,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE,
                FOREIGN KEY (grammar_id) REFERENCES grammars(id) ON DELETE CASCADE,
                PRIMARY KEY (query_id, grammar_id)
        )""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS lookup_translations (
                grammar_id INTEGER,
                translation_id INTEGER,
                FOREIGN KEY (grammar_id) REFERENCES grammar(id) ON DELETE CASCADE,
                FOREIGN KEY (translation_id) REFERENCES translations(id) ON DELETE CASCADE,
                PRIMARY KEY (grammar_id, translation_id)
        )""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS lookup_examples (
                grammar_id INTEGER,
                example_id INTEGER,
                FOREIGN KEY (grammar_id) REFERENCES grammar(id) ON DELETE CASCADE,
                FOREIGN KEY (example_id) REFERENCES examples(id) ON DELETE CASCADE,
                PRIMARY KEY (grammar_id, example_id)
        )""")

        cursor.execute("""
            SELECT
                g.id,
                g.category,
                g.domain,
                g.meaning
            FROM
                queries q
            JOIN
                lookup_grammar lg ON q.id = lg.query_id
            JOIN
                grammars g ON lg.grammar_id = g.id
            WHERE
                q.text = ?;
        """,
                       (query,))

        grammars = cursor.fetchall()

        for grammar in grammars:
            grammar_id, category, domain, meaning = grammar
            grammar = Grammar(category, domain, meaning)

            cursor.execute("""
                SELECT
                    t.quote,
                    t.category,
                    t.grammar
                FROM 
                    grammars g
                JOIN 
                    lookup_translations lt ON g.id = lt.grammar_id
                JOIN 
                    translations t ON lt.translation_id = t.id
                WHERE 
                    g.id = ?;
            """,
                           (grammar_id,))

            translations = cursor.fetchall()

            for i, translation in enumerate(translations):
                translations[i] = Translation(*translation)

            cursor.execute("""
                SELECT
                    e.original,
                    e.translations
                FROM 
                    grammars g
                JOIN 
                    lookup_examples le ON g.id = le.grammar_id
                JOIN 
                    examples e ON le.example_id = e.id
                WHERE 
                    g.id = ?;
            """,
                           (grammar_id,))

            examples = cursor.fetchall()

            for i, example in enumerate(examples):
                examples[i] = Example(*example)

            results.append(Entry(query, grammar, translations, examples))

    return results


def store_to_cache(query: list[str], entries: list[Entry]) -> None:
    if not entries:
        return

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    query: str = ' '.join(query)

    with sqlite3.connect(CACHE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO queries (text)
            VALUES (?)
        """,
                       (query,))

        query_id: int = cursor.lastrowid

        for entry in entries:
            grammar = entry.grammar

            cursor.execute("""
                INSERT OR IGNORE INTO grammars (category, domain, meaning)
                VALUES (?, ?, ?)
            """,
                           (grammar.category, grammar.domain, grammar.meaning))

            grammar_id: int = cursor.lastrowid

            cursor.execute("""
                INSERT OR IGNORE INTO lookup_grammar (query_id, grammar_id)
                VALUES (?, ?)
            """,
                           (query_id, grammar_id))

            for translation in entry.translations:
                cursor.execute("""
                    INSERT OR IGNORE INTO translations (quote, category, grammar)
                    VALUES (?, ?, ?)
                """,
                               (translation.quote, translation.category, translation.grammar))

                trans_id: int = cursor.lastrowid

                cursor.execute("""
                    INSERT OR IGNORE INTO lookup_translations (grammar_id, translation_id)
                    VALUES (?, ?)
                """,
                               (grammar_id, trans_id))

            for example in entry.examples:
                cursor.execute("""
                    INSERT OR IGNORE INTO examples (original, translations)
                    VALUES (?, ?)
                """,
                               (example.original, example.translations))

                exam_id: int = cursor.lastrowid

                cursor.execute("""
                    INSERT OR IGNORE INTO lookup_examples (grammar_id, example_id)
                    VALUES (?, ?)
                """,
                               (grammar_id, exam_id))


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
