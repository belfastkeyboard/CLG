from pathlib import Path
import os
from entry import Entry, Example, Grammar, Translation
import sqlite3

CACHE = Path(os.path.dirname(os.path.abspath(__file__)), '.cache')


def get_from_cache(query: list[str], site: str) -> list[Entry]:
    CACHE.mkdir(parents=True, exist_ok=True)
    query = ' '.join(query)
    results: list[Entry] = []

    database = Path(CACHE, f'{site}.db')

    with sqlite3.connect(database) as conn:
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


def store_to_cache(query: list[str], entries: list[Entry], site: str) -> None:
    if not entries:
        return

    CACHE.mkdir(parents=True, exist_ok=True)
    query: str = ' '.join(query)

    database = Path(CACHE, f'{site}.db')

    with sqlite3.connect(database) as conn:
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
