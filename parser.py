from bs4 import BeautifulSoup
import json
import os
import posixpath
import requests
from urllib.parse import urlsplit, unquote

HEADERS = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
           'accept': '*/*'}
URL = 'https://qdpro.com.ua/uk/uktzed'
HOST = 'https://qdpro.com.ua'
def get_soup(url, **kwargs):
    response = requests.get(url, headers=HEADERS, **kwargs)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features='html.parser')
    else:
        soup = None
    return soup

def dump_to_json(filename, data, **kwargs):
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 1)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, **kwargs)


def getDataFromJsonFile(jsonfilename):
    data = []

    jsonfilename = '{0}\\{1}'.format(CURR_DIR, jsonfilename)

    if os.path.exists(jsonfilename):
        with open(jsonfilename, encoding='utf-8') as json_file:
            data = json.load(json_file)
    return data

class Uktzd:
    def __init__(self, id=None, url=None, name=None, nomLevel=0):
        self.id = id
        self.url = url
        self.name = name
        self.nomLevel = nomLevel
        self.separateChar = ''
        self.level2Code = ''
        self.childs = None

class UktzdTree:
    def __init__(self, url: str):
        self.uktzds = list[Uktzd]
        self.url = url
        self._firstlevel()
        #self._parstree(self.uktzds)

    def Firstlevel(self) -> list[Uktzd]:
        uktzds = [uktzd for uktzd in self.uktzds if uktzd.nomLevel == 0]
        return uktzds

    def ParsTreeByUktzd(self, uktzd:Uktzd):
        uktzds = [u for u in self.uktzds if u.id == uktzd.id]
        self._parstree(uktzds)
        uktzds = [u for u in self.uktzds if u.id == uktzd.id]
        return uktzds
    def _get_level(self, url:str, parent:Uktzd=None) -> list[Uktzd]:
        html = get_soup(url)
        descr = html.find('div', class_='qdfolio')
        uktzds = []
        nomLevel = parent.nomLevel+1 if not parent is None else 0
        level2Code = parent.level2Code if not parent is None else ''
        if descr is None:
            return uktzds

        if descr.findAll('table', class_='sticky-enabled').__len__() > 1:
            descr = descr.findAll('table', class_='sticky-enabled')
            descr = descr[1]

        headers = descr.find('tbody').findAll('tr')

        if headers.__len__() > 0:
            for row in headers:
                idlist = row.find('a').get_text(strip=True)
                idlist = idlist.replace('[','')
                idlist = idlist.replace(']', '')
                namelist = row.findAll('td')[1].get_text(strip=True)
                href = row.find('a').get('href')
                url = '{0}{1}'.format(HOST, href)

                uktzd = Uktzd(idlist, url, namelist, nomLevel)

                uktzd.level2Code = level2Code

                if nomLevel == 1:
                    uktzd.level2Code = idlist.replace('Група ','')

                if idlist.find('-') == 0 and nomLevel > 2:
                    uktzd.separateChar = parent.separateChar+'- '

                if idlist.find(uktzd.separateChar+uktzd.level2Code) == 0 or nomLevel < 3:
                    uktzds.append(uktzd)

        return uktzds
    def _firstlevel(self):
        uktzds = self._get_level(self.url)
        self.uktzds = uktzds.copy()

    def _parstree(self, childs:list[Uktzd]) -> None:

        for child in childs:
            print(child.id)
            uktzds = self._get_level(child.url, child)

            if not uktzds:
                continue

            child.childs = uktzds

            self._parstree(child.childs)

from json import JSONEncoder
class DataEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

CURR_DIR = os.getcwd()

def dumps_to_json(filename, data, **kwargs):
    #print(json.dumps(data, cls=clsEncode))
    filename = '{0}\\{1}'.format(CURR_DIR, filename)
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 1)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=DataEncoder, **kwargs)

def pars_html(url):
    uktzdTree = UktzdTree(url)
    firstLevelUktzds = uktzdTree.Firstlevel()

    for uktzd in firstLevelUktzds:
        filename = 'uktzd_{0}.json'.format(uktzd.id)
        data = getDataFromJsonFile(filename)
        if data.__len__() < 1:
            data = uktzdTree.ParsTreeByUktzd(uktzd)
            dumps_to_json(filename, data)
    return data
def main():
    pars_html(URL)

if __name__ == '__main__':
    main()