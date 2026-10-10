"""Nested document browser and keyword search."""
import argparse
import pydoc
import re
import subprocess
import sys
from . import __version__
from .answers import answer_question
from .reference import SECTIONS, get_text, get_topic, list_topics, search_topics, export_pdf, open_pdf


def highlight(text, keyword, color=False):
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: ('\033[1;33m' + m[0] + '\033[0m') if color else '[[' + m[0] + ']]', text)


def display(section, topic=None, plain=False, keyword=None):
    title = SECTIONS[section][0]
    body = get_text(section) if topic is None else get_topic(section, topic)
    if topic is not None:
        title += ' / ' + list_topics(section)[topic - 1]['title']
    # Markers remain visible even in Windows pagers that strip ANSI escapes.
    text = title + '\n' + '=' * 60 + '\n\n' + highlight(body, keyword)
    if keyword:
        text = f'Search: {keyword} (matches marked with [[...]]).\n\n' + text
    if plain or not sys.stdout.isatty():
        print(text)
    else:
        pydoc.pager(text)


def display_theory(plain=False):
    """Show both complete theory documents in one continuous reading view."""
    parts = ['THEORY - Full Unit 2 and Unit 5']
    for section in (1, 2):
        parts.append(SECTIONS[section][0] + '\n' + '=' * 60 + '\n\n' + get_text(section))
    text = '\n\n'.join(parts)
    if plain or not sys.stdout.isatty():
        print(text)
    else:
        pydoc.pager(text)


def ask(prompt):
    return input(prompt).strip()


def search_menu(section, plain=False, query=None):
    if query is None:
        query = ask('Keyword (blank to cancel): ')
    if not query.strip():
        return
    results = search_topics(query, section)
    if not results:
        print('No matches found in this document.')
        return
    while True:
        print(f'\nSearch results in {SECTIONS[section][0]} for "{query}"')
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} ({len(result['matches'])} matching lines)")
            for line, snippet in result['matches'][:2]:
                print(f'   Line {line}: {highlight(snippet, query)}')
        print('0. Back to document contents')
        choice = ask('Open result: ')
        if choice == '0':
            return
        if choice.isdigit() and 1 <= int(choice) <= len(results):
            display(section, results[int(choice) - 1]['topic'], plain, query)
            return
        else:
            print('Choose a result number or 0.')


def show_answer(question, section=None, plain=False):
    text = answer_question(question, section)['answer']
    if plain or not sys.stdout.isatty():
        print(text)
    else:
        pydoc.pager(text)


def answer_menu(section=None, plain=False):
    scope = SECTIONS[section][0] if section is not None else 'all documents'
    print(f'Answer a question - {scope}')
    while True:
        question = ask('Question (0 or blank to go back): ')
        if question in ('', '0'):
            return
        show_answer(question, section, plain)


def document_menu(section, plain=False):
    topics = list_topics(section)
    while True:
        print('\n' + SECTIONS[section][0] + ' - Contents\n' + '=' * 60)
        for number, item in enumerate(topics, 1):
            indent = '  ' if item['level'] == 2 else ''
            print(f"{number}. {indent}{item['title']}")
        print('S. Search this document')
        print('A. Answer a question from this document')
        print('0. Back to documents')
        choice = ask('Select a section, S to search, or A to ask: ').lower()
        if choice == '0':
            return
        if choice == 's':
            search_menu(section, plain)
        elif choice == 'a':
            answer_menu(section, plain)
        elif choice.isdigit() and 1 <= int(choice) <= len(topics):
            display(section, int(choice), plain)
        else:
            print('Choose a section number, S, A, or 0.')


def menu(plain=False, pdf=False):
    while True:
        print('\nTHUK\n' + '=' * 42)
        for number, (title, _) in SECTIONS.items():
            print(f'{number}. {title}')
        answer_option = max(SECTIONS) + 1
        print(f'{answer_option}. Answer a question')
        print('F. Theory (full Unit 2 + Unit 5)')
        print('0. Exit\n' + '=' * 42)
        choice = ask(f'Select an option (1-{answer_option}, F): ').lower()
        if choice == '0':
            return 0
        if choice == 'f':
            display_theory(plain)
            continue
        if choice in (str(answer_option), 'a'):
            answer_menu(plain=plain)
            continue
        if choice not in {str(n) for n in SECTIONS}:
            print(f'Choose an option from 1 to {answer_option}, F for theory, or 0 to exit.')
            continue
        if pdf:
            try:
                print(f'Opened: {open_pdf(int(choice))}')
            except (ValueError, OSError, subprocess.CalledProcessError) as exc:
                print(f'Cannot open PDF: {exc}')
        else:
            document_menu(int(choice), plain)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Thuk offline document browser')
    parser.add_argument('section', nargs='?', type=int, choices=SECTIONS, help=f'document number (1-{max(SECTIONS)})')
    parser.add_argument('--topic', type=int, help='read one topic by its contents-menu number')
    parser.add_argument('--version', action='version', version=f'Thuk {__version__}')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--pdf', action='store_true', help='open the original PDF')
    group.add_argument('--export-pdf', metavar='PATH', help='save the original PDF')
    group.add_argument('--search', metavar='TEXT', help='search the selected document, or all documents')
    group.add_argument('--ask', metavar='QUESTION', help='answer from offline note excerpts, optionally within a document')
    group.add_argument('--full', action='store_true', help='print the complete document')
    parser.add_argument('--plain', action='store_true', help='disable the interactive pager')
    args = parser.parse_args(argv)
    if (args.topic is not None or args.export_pdf or args.full) and args.section is None:
        parser.error('--topic, --export-pdf and --full require a document number')
    if args.topic is not None and (args.pdf or args.export_pdf or args.full or args.search is not None or args.ask is not None):
        parser.error('--topic cannot be combined with PDF, full-document, search or answer options')
    try:
        if args.ask is not None:
            show_answer(args.ask, args.section, args.plain)
        elif args.search is not None:
            if not args.search.strip():
                raise ValueError('Enter a non-empty search query.')
            if args.section is not None and sys.stdin.isatty():
                search_menu(args.section, args.plain, args.search)
                document_menu(args.section, args.plain)
            else:
                found = False
                for section in ([args.section] if args.section else SECTIONS):
                    for result in search_topics(args.search, section):
                        found = True
                        print(f"{SECTIONS[section][0]} / {result['title']} (topic {result['topic']})")
                        for line, snippet in result['matches']:
                            print(f'  {line}: {highlight(snippet, args.search)}')
                if not found:
                    print('No matches found.')
        elif args.section is None:
            return menu(args.plain, args.pdf)
        elif args.export_pdf:
            print(export_pdf(args.section, args.export_pdf))
        elif args.pdf:
            print(f'Opened: {open_pdf(args.section)}')
        elif args.topic is not None or args.full:
            display(args.section, args.topic, args.plain)
        else:
            document_menu(args.section, args.plain)
        return 0
    except (EOFError, KeyboardInterrupt, BrokenPipeError):
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Thuk: {exc}', file=sys.stderr)
        return 1

