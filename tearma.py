from bs4 import BeautifulSoup, ResultSet, Tag
from entry import Entry, Example, Grammar, Translation


def get_tearma_grammar(entry: Tag) -> Grammar:
    domain: str = entry.find('div', class_='prettyDomain').find('div', class_='left').text.split(' » ')[0]
    category: str = entry.find('span', class_='label').text
    meaning: Tag = entry.find('div', class_='intro')

    meaning: str = meaning.text.strip('()') if meaning else ''

    return Grammar(category, domain, meaning)


def get_tearma_translations(entry: Tag) -> list[Translation]:
    results: list[Translation] = []

    entries: ResultSet = entry.find_all('div', attrs={'class': 'prettyDesig', 'data-lang': 'ga'})

    for entry in entries:
        quote: str = entry.attrs.get('data-wording')
        grammar: str = entry.find('span', class_='label').text
        category: Tag = entry.find('span', class_='accept')

        category: str = category.text.split('/')[0] if category else ''

        results.append(Translation(quote, category, grammar))

    return results


def get_tearma_examples(entry: Tag) -> list[Example]:
    results: list[Example] = []

    entries: ResultSet = entry.find_all('div', class_='prettyExample')

    for entry in entries:
        original: str = entry.find('div', class_='left').text.strip()
        translations: str = entry.find('div', class_='right').text.strip()

        results.append(Example(original, translations))

    return results


def get_tearma_entry(query: str, entry: Tag) -> Entry:
    grammar = get_tearma_grammar(entry)
    translations = get_tearma_translations(entry)
    examples = get_tearma_examples(entry)

    return Entry(query, grammar, translations, examples)


def get_from_tearma(query: str, soup: BeautifulSoup) -> list[Entry]:
    main: Tag = soup.find('main', id='main')
    results: list[Entry] = []

    for child in main.children:
        if isinstance(child, Tag):
            classes: list[str] = child.attrs.get('class')

            if not any([c for c in classes if c in ['sectitle', 'prettyEntry']]):
                continue

            if 'sectitle' in classes and 'Related matches' in child.text:
                break

            if 'prettyEntry' in classes:
                entry: Entry = get_tearma_entry(query, child)
                results.append(entry)

    return results
