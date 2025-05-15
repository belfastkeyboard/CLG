class Grammar:
    def __init__(self, category: str, domain: str, meaning: str):
        self.category: str = category
        self.domain: str = domain
        self.meaning: str = meaning

    def __repr__(self):
        return f'Grammar(category={self.category}, domain={self.domain}, meaning={self.meaning})'


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


class Entry:
    def __init__(self, original: str, grammar: Grammar, translations: list[Translation], examples: list[Example]):
        self.original: str = original
        self.grammar: Grammar = grammar
        self.translations: list[Translation] = translations
        self.examples: list[Example] = examples

    def __repr__(self):
        return (f'Entry(original={self.original}, grammar={self.grammar}, translations={self.translations}, '
                f'examples={self.examples})')
