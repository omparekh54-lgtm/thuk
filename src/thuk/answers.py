"""Offline, extractive answers from the bundled references only."""
import math
import re
from collections import Counter

from .reference import SECTIONS, get_text, list_topics

_STOP = set('a an the is are was were be been being what which who where when why how '
            'do does did can could would should will shall i me my you your we our it its '
            'this that these those of for to in on at by from with and or as about '
            'please explain describe tell give show answer question command commands use using used '
            'difference differences between versus vs compare comparison'.split())
_ALIASES = {'vm': ('virtual', 'machine'), 'vms': ('virtual', 'machine'),
            'mvt': ('model', 'view', 'template'), 'drf': ('django', 'rest', 'framework'),
            'db': ('database',), 'k8s': ('kubernetes',)}


def _terms(text):
    result = []
    for word in re.findall(r'[a-z0-9]+', text.casefold()):
        if word in _STOP:
            continue
        words = _ALIASES.get(word, (word,))
        for term in words:
            if len(term) > 4 and term.endswith('s') and not term.endswith(('ss', 'is', 'us')):
                term = term[:-1]
            result.append(term)
    return result


def answer_question(question, section=None, limit=3):
    """Return a sourced extractive answer; no model, network or code execution.

    Result fields: question, found, answer and sources. Each source contains
    section, document, topic, title, line_start, line_end and an exact excerpt.
    A lexical match is evidence of relevance, not proof of a complete answer.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError('Enter a non-empty question.')
    if section is not None and section not in SECTIONS:
        raise ValueError('Choose a section from 1 to 5.')
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 5:
        raise ValueError('Choose an answer limit from 1 to 5.')
    query = set(_terms(question))
    result = {'question': question.strip(), 'found': False, 'answer': '', 'sources': []}
    if not query:
        result['answer'] = 'Please include a study topic in your question, such as Django migrations.'
        return result
    passages = []
    for number in ([section] if section is not None else SECTIONS):
        lines = get_text(number).splitlines()
        for topic, item in enumerate(list_topics(number), 1):
            if item['title'] == 'Document introduction':
                continue
            # Overlap retains context across PDF page/paragraph boundaries.
            for start in range(item['start'], item['end'], 18):
                end = min(start + 30, item['end'])
                while start < end and not lines[start].strip():
                    start += 1
                while end > start and not lines[end - 1].strip():
                    end -= 1
                excerpt = '\n'.join(lines[start:end])
                words = _terms(excerpt)
                if len(words) < 5:
                    continue
                passages.append({'section': number, 'document': SECTIONS[number][0],
                                 'topic': topic, 'title': item['title'], 'line_start': start + 1,
                                 'line_end': end, 'excerpt': excerpt, '_counts': Counter(words)})
    frequency = Counter()
    for passage in passages:
        frequency.update(passage['_counts'].keys())
    total = len(passages)
    average = sum(sum(p['_counts'].values()) for p in passages) / max(total, 1)
    ranked = []
    for passage in passages:
        counts = passage['_counts']
        matches = query.intersection(counts)
        coverage = len(matches) / len(query)
        # Refuse unrelated and weak matches, rather than guessing from one word.
        if coverage < 1.0:
            continue
        length = sum(counts.values())
        score = 0.0
        for term in matches:
            idf = math.log(1 + (total - frequency[term] + 0.5) / (frequency[term] + 0.5))
            tf = counts[term]
            score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * length / average))
        score *= coverage
        # For explanations prefer theory; for commands prefer the code references.
        wants_code = bool(re.search(r'\b(command|commands|code|syntax)\b', question, re.I))
        if (passage['section'] >= 3) == wants_code:
            score *= 1.15
        ranked.append((score, passage))
    ranked.sort(key=lambda pair: (-pair[0], pair[1]['section'], pair[1]['line_start']))
    for _, passage in ranked:
        if any(passage['section'] == old['section'] and
               max(passage['line_start'], old['line_start']) <= min(passage['line_end'], old['line_end'])
               for old in result['sources']):
            continue
        source = {key: value for key, value in passage.items() if not key.startswith('_')}
        # Avoid repeating identical passages shared by two documents.
        if any(source['excerpt'] == old['excerpt'] for old in result['sources']):
            continue
        result['sources'].append(source)
        if len(result['sources']) == limit:
            break
    result['found'] = bool(result['sources'])
    if not result['found']:
        result['answer'] = ('I could not find enough matching material in the bundled notes. '
                            'Try a more specific question or use the terms from your notes.')
    else:
        parts = ['Relevant passages from your notes (offline excerpts, not an AI explanation):']
        for index, source in enumerate(result['sources'], 1):
            parts.append(f"[{index}] {source['document']} / {source['title']} "
                         f"(topic {source['topic']}, lines {source['line_start']}-{source['line_end']})"
                         + '\n\n' + source['excerpt'])
        result['answer'] = '\n\n'.join(parts)
    return result
