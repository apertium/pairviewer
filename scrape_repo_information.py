from bs4 import BeautifulSoup
import urllib.request
import pdb
import xml.etree.ElementTree as xml
import argparse, urllib.request
import json
"""
Script to scrape text from GitHub and into JSON format for all language pairs in Apertium.
Stem counter by sushain
"""

with open('pairs.json', 'a') as f:
    f.write('[')

class Pair:
    def __init__(self, lg1, lg2, last_updated, created, direction, repo, stems):
        self.lg1 = lg1 #done
        self.lg2 = lg2 #done
        self.last_updated = last_updated
        self.created = created
        self.direction = direction #done
        self.repo = repo #done
        self.stems = stems #done

types = ["trunk", "incubator", "nursery", "staging"]

def print_info(uri, bidix=None):
    returned = get_info(uri, bidix)
    if "stems" in returned:
        return returned['stems']
    if "paradigms" in returned:
        print('Paradigms: %s' % returned['paradigms'])

def get_info(uri, bidix=None):
    dictX = ""
    if "http" in uri:
        try:
            dictX = str((urllib.request.urlopen(uri)).read(), 'utf-8')
        except:
            return -1 # FIXME: error handling

    else:
        dictX = (open(uri, 'r')).read()
    try:
        tree = xml.fromstring(dictX)
    except:
        return -1  # FIXME: error handling

    if bidix is not None:
        bi = bidix
    else:
        bi = len(tree.findall("pardefs")) == 0 #bilingual dicts don't have pardefs section -- not necessarily true? check /trunk/apertium-en-es/apertium-en-es.en-es.dix

    bi = True
    out = {}
    if(bi):
        out['stems'] = len(tree.findall("*[@id='main']/e//l"))
        #print('Stems: %s ' % len(tree.findall("*[@id='main']/e//l")))
    else:
        #print('Stems: %s' % len(tree.findall("section/*[@lm]")))  # there can be sections other than id="main"
        out['stems'] = len(tree.findall("section/*[@lm]"))  # there can be sections other than id="main"
        if tree.find('pardefs') is not None:
            #print('Paradigms: %s' % len(tree.find('pardefs').findall("pardef")))
            out['paradigms'] = len(tree.find('pardefs').findall("pardef"))
    return out

for x in types:
    html_data = urllib.request.urlopen('https://github.com/apertium/apertium-'+x)
    html = html_data.read()
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    tr = soup.find_all('tr')
    for i in tr:
        try:
            if "apertium" in i.find_all('td')[1].text:
                lg1 = ""
                lg2 = ""
                direction = ""
                created = ""
                last_updated = ""
                yummy = x
                stems = 0

                td_element = i.find_all('td')[1]
                link = td_element.find("span").find('a')['href']

                #getting names
                text = td_element.text
                important = text.split('@')[0]
                lang_pair_text = important
                important = important.split('-')
                lg1 = important[1]
                lg2 = important[2]

                #getting into repository
                repo_html_data = urllib.request.urlopen('https://github.com'+link).read()
                repo_soup = BeautifulSoup(repo_html_data, 'html.parser')
                repo_table = repo_soup.find('table')
                repo_tr = repo_table.find_all('tr')
                number_of_commits = int(repo_soup.find('span', {'class': 'num text-emphasized'}).text.strip().replace(',', ""))-2
                for row in repo_tr:
                    name = row.find_all('td')[1].text
                    if str(name.strip()) == str("modes.xml"):
                        modes_link = row.find_all('td')[1].find("span").find('a')['href']
                        modes_html = urllib.request.urlopen('https://github.com'+modes_link).read()
                        modes_repo_soup = BeautifulSoup(modes_html, 'html.parser')
                        modes_repo_lang_pairs = modes_repo_soup.find_all('span', {"class":"pl-s"})
                        for pair in modes_repo_lang_pairs:
                            if len(pair.text.split("-")) == 2:
                                arr = pair.text.split("-")
                                if arr[0].strip().replace('\"', "") == lg1.strip() and arr[1].strip().replace('\"', "") == lg2.strip():
                                    direction += "<"
                                elif arr[0].strip().replace('\"', "") == lg2.strip() and arr[1].strip().replace('\"', "") == lg1.strip():
                                    direction += ">"
                        if direction == "><":
                            direction = "<>"
                    elif ".dix" in str(name.strip()):
                        modes_link = row.find_all('td')[1].find("span").find('a')['href']
                        modes_html = urllib.request.urlopen("https://github.com"+modes_link).read()
                        modes_repo_soup = BeautifulSoup(modes_html, 'html.parser')
                        modes_repo_lang_pairs = modes_repo_soup.find_all('a')
                        for pair in modes_repo_lang_pairs:
                            if pair.text.strip() == "Raw" or pair.text.strip() == "View Raw":
                                try:
                                    stems = print_info("https://github.com"+pair['href'], bidix=True)
                                except:
                                    pass
                #last updated
                commits_link = 'https://github.com/'+'apertium/'+lang_pair_text.strip()+"/commits"
                commits_html = urllib.request.urlopen(commits_link).read()
                commits_repo_soup = BeautifulSoup(commits_html, 'html.parser')
                commits_repo_lang_pairs = commits_repo_soup.find_all('div', {"class":"commit-group-title"})
                last_updated = (commits_repo_lang_pairs[0].text).replace("Commits on", "").strip()

                #initial commit
                current_page = commits_repo_soup
                for y in current_page.find_all('a'):
                    if y.text == "Older":
                        next_page = y['href']
                        splitted = y['href'].split('+')[0]
                        next_page = splitted + '+' + str(number_of_commits)
                        next_page_html = urllib.request.urlopen(next_page).read()
                        current_page = BeautifulSoup(next_page_html, 'html.parser')
                        pairs = current_page.find_all('div', {"class":"commit-group-title"})
                        created = (pairs[-1].text).replace("Commits on", "").strip()

                pair = Pair(created=created, last_updated=last_updated, lg1=lg1.strip(), lg2=lg2.strip(), direction=direction, repo=yummy, stems=stems)
                with open('pairs.json', 'a') as f:
                    f.write(json.dumps(pair, default=lambda o: o.__dict__))
                    f.write(",\n")
                    print(json.dumps(pair, default=lambda o: o.__dict__))
                    f.close()
                    
        except IndexError:
            pass

with open('pairs.json', 'a') as f:
    f.write(']')
