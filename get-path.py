import datetime
import re

import bs4
import requests

WIKI_PREFIX = 'https://ru.wikipedia.org/wiki/'
URL = "https://ru.wikipedia.org/w/api.php"

S = requests.Session()


def get_links(filename) -> tuple:
    with open(filename) as f:
        links = [link.strip() for link in f.readlines()]
    return links[0].rsplit('/')[-1], links[1].rsplit('/')[-1]


def query(request):
    request['action'] = 'query'
    request['format'] = 'json'
    lastContinue = {}
    while True:
        # Clone original request
        req = request.copy()
        # Modify it with the values returned in the 'continue' section of the last result.
        req.update(lastContinue)
        # Call API
        result = S.get(URL, params=req).json()

        if 'error' in result:
            raise Exception(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'query' in result:
            yield result['query']
        if 'continue' not in result:
            break
        lastContinue = result['continue']


def get_page_links(title):
    links = set()
    with open('log.txt', 'a') as f:
        f.write(f'Getting {title} page links')
        f.write('\n')
    for result in query({
        "titles": title,
        "prop": "links",
        "pllimit": "max"
    }):
        for k, v in result['pages'].items():
            if v.get("links"):
                for link in v.get("links"):
                    links.add(link["title"])
    return links


def get_page_backlinks(title):
    backlinks = set()
    with open('log.txt', 'a') as f:
        f.write(f'Getting {title} page backlinks')
        f.write('\n')
    for result in query({
        "list": "backlinks",
        "bltitle": title
    }):
        for backlink in result.get('backlinks'):
            backlinks.add(backlink["title"])
    return backlinks


def middle(links, backlinks):
    intersection = links & backlinks
    if intersection:
        return [intersection.pop()]
    for link in links:
        with open('log.txt', 'a') as f:
            f.write(link)
            f.write('\n')
        sublinks = get_page_links(link)
        for sublink in sublinks:
            if sublink in backlinks:
                return [link, sublink]
    return


def format_output(path):
    if not path:
        return ['There is no path']
    path_with_spaces = list(map(lambda x: x.replace('_', ' '), path))
    result = []
    for i, title in enumerate(path_with_spaces[:-1]):
        result.append(f"{i + 1}------------------------")
        response = S.get(WIKI_PREFIX + title)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, features='html.parser')
        link = soup.find('a', title=path_with_spaces[i + 1])
        text = link.parent.text + ' '
        sentences = re.split(r'[.!?]+\s', text)
        for s in sentences:
            if link.text in s:
                result.append(s)
                break
        result.append(WIKI_PREFIX + path[i + 1].replace(' ', '_'))
    return result


def link_path(filename):
    with open('log.txt', 'w') as f:
        f.write(str(datetime.datetime.now()) + '\n')
    source, target = get_links(filename)
    links = get_page_links(source)
    if target in links:
        path = [source, target]
    else:
        backlinks = get_page_backlinks(target)
        path_middle = middle(links, backlinks)
        if path_middle:
            path = [source, *path_middle, target]
        else:
            path = None
    result = format_output(path)
    with open('log.txt', 'a') as f:
        f.writelines('\n'.join(result))
        f.write('\n')
    return result


if __name__ == '__main__':
    print(*link_path('input.txt'), sep='\n')