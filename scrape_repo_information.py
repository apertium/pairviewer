from bs4 import BeautifulSoup
import urllib.request
import pdb
import xml.etree.ElementTree as xml
import argparse, urllib.request
import json
import collections
import time

"""
Script to scrape text from GitHub and into JSON format for all language pairs in Apertium.
Stem counter by sushain
"""


pairs = []
Pair = collections.namedtuple('Pair', 'lg1 lg2 last_updated created direction repo stems')

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
    else:
        out['stems'] = len(tree.findall("section/*[@lm]"))  # there can be sections other than id="main"
        if tree.find('pardefs') is not None:
            out['paradigms'] = len(tree.find('pardefs').findall("pardef"))
    return out




for x in types:
    html_data = urllib.request.urlopen('https://api.github.com/repos/apertium/apertium-'+x+'/'+'contents')
    html = json.loads(html_data.read())
    for i in html:
        try:
            if "apertium" in i["name"]:
                lg1 = ""
                lg2 = ""
                direction = ""
                created = ""
                last_updated = ""
                repo_name = x
                stems = 0

                lang_pair_name = i["name"]
                #link = i["download_url"]

                #getting names
                important = lang_pair_name.split('-')
                lg1 = important[1]
                lg2 = important[2]

                #getting into repository
                link = "https://api.github.com/repos/apertium/"+lang_pair_name+"/contents"
                repo_json = json.loads(urllib.request.urlopen(link).read())
                for el in repo_json:
                    if el["name"] == "modes.xml":
                        download_url = el["download_url"]
                        html_for_blob = urllib.request.urlopen(download_url).read()
                        if lg1+'-'+lg2 in str(html_for_blob):
                            direction += "<"
                        if lg2+'-'+lg1 in str(html_for_blob):
                            direction += ">"

                    elif ".dix" in el["name"]:
                        stems = print_info(el["download_url"], bidix=True)

                    if direction == "><":
                        direction = "<>"

                commits_link = 'https://api.github.com/'+'repos/apertium/'+lang_pair_name.strip()+"/commits"
                commits_html = urllib.request.urlopen(commits_link).read()

                last_updated = json.loads(commits_html)[0]["commit"]["committer"]["date"]
                created = json.loads(commits_html)[-1]["commit"]["committer"]["date"]

                pair = Pair(created=created, last_updated=last_updated, lg1=lg1.strip(), lg2=lg2.strip(), direction=direction, repo=repo_name, stems=stems)
                print(json.dumps(pair, default=lambda o: o.__dict__))
                pairs.append(pair)
                time.sleep(3) #if you change this value you will get blocked likely
        except:
            pass

with open('pairs.json', 'a') as f:
    json_string = json.dumps([ob.__dict__ for ob in pairs])
