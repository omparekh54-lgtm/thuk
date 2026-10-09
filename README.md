# Thuk

An offline Python study library with a nested terminal browser for five documents:

1. Unit 2 Theory
2. Unit 5 Theory
3. Django Code (complete Unit 2 coding reference)
4. Docker Commands (complete Unit 5 coding reference)
5. Git Commands (supplementary cheat sheet)

The full supplied text and all four original PDFs are bundled. No runtime dependencies, API keys or internet access are needed after installation. Code and commands in references are displayed for reading, never executed.

## Install and run

Python 3.9 or newer and Git:

```powershell
python -m pip install git+https://github.com/omparekh54-lgtm/thuk.git
python -m thuk
```

Install while your virtual environment is active if you want to use Thuk inside it. The `thuk` command also works when your Python Scripts directory is on PATH (normally automatic in an active virtual environment).

Without Git, download the repository ZIP, extract it, open a terminal inside the extracted folder, and run `python -m pip install .`.

Not published to PyPI yet.

## Browse

```text
THUK
==========================================
1. Unit 2 Theory
2. Unit 5 Theory
3. Django Code
4. Docker Commands
5. Git Commands
0. Exit
```

Choose a document to see its contents, with numbered chapters and subsections. Choose a topic to read only that topic. Chapters include their subsections; choosing a subsection reads just that subsection.

After reading, you stay in the same document's contents menu. In an interactive pager, press `q` to finish reading. Choose `0. Back to documents` to return to the five-document menu; `0. Exit` there closes Thuk. Ctrl+C or end-of-input exits cleanly.

A `Document introduction` entry preserves each document's preface and original contents page. PDF extraction can change table spacing; open the original PDF to see diagrams and exact formatting.

## Search within a document

Choose `S. Search this document`, then type a keyword or phrase such as `migrations` or `docker run`. Search is case-insensitive and treats the query literally.

Thuk lists matching sections with match counts and preview lines. Choose a result to open its section. Every matching keyword in that section is highlighted as `[[keyword]]`, which is readable on Windows, Linux and macOS. After reading a search result you return to that document's contents. `0` at search results returns without opening a result; a blank query cancels search.

Search maps each hit to the most specific subsection, so parent chapters don't duplicate subsection results. Contents-page hits appear under Document introduction.

## Other commands

```powershell
thuk 1                           # Open Unit 2's contents menu
thuk 3                           # Open the Django code contents menu
thuk 3 --topic 2 --plain          # Print topic 2 and exit
thuk 1 --full --plain             # Print the entire document
thuk 3 --search migrations        # Interactive document search
thuk --search Docker             # Print matches across all documents
thuk 1 --pdf                      # Open the original PDF in your desktop viewer
thuk 4 --export-pdf docker.pdf    # Save the original PDF
```

Use `python -m thuk` instead of `thuk` if the executable isn't on PATH. In piped/noninteractive CLI search, results are printed with topic numbers; open one using `--topic NUMBER`. PDF export replaces the destination file if it exists. Git is a text-only reference and has no source PDF.

## Python API

```python
from thuk import get_text, list_topics, get_topic, search_topics

print(list_topics(1))
print(get_topic(1, 2))
print(search_topics('Django', 1))
print(get_text(1))
```

## Development

```sh
python -m pip install .
python -m unittest discover -s tests -v
python -m pip wheel --no-deps . -w dist
```

The topic index is stored in `src/thuk/data/contents.json` using zero-based start and exclusive end line offsets in the bundled text. Update that index whenever reference text line boundaries change. The four original PDFs retain their source authorship.
