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
types = ["trunk", "nursery", "incubator", "staging"]

def print_info(uri):
    returned = get_info(uri)
    return returned

def get_info(uri):
    try:
        dictX = str((urllib.request.urlopen(uri)).read(), 'utf-8')
        tree = xml.fromstring(dictX)
    except:
        return -1 # FIXME: error handling

    return len(tree.findall("*[@id='main']/e//l"))

for x in types:
    html_url = "https://api.github.com/repos/apertium/apertium-%s/contents" % x
    html_data = urllib.request.urlopen(html_url)
    html = json.loads(html_data.read())
    for i in html:
        if "apertium" in i["name"]:
            try:
                repo_name = x
                direction = ""
                lang_pair_name = i["name"]
                #getting names
                lg1 = lang_pair_name.split('-')[1]
                lg2 = lang_pair_name.split('-')[2]
                #getting into repository
                link = "https://api.github.com/repos/apertium/%s/contents" % lang_pair_name
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
                        stems = print_info(el["download_url"])
                    if direction == "><":
                        direction = "<>"
                commits_link = "https://api.github.com/repos/apertium/%s/commits" % lang_pair_name
                commits_html = urllib.request.urlopen(commits_link).read()
                last_updated = json.loads(commits_html)[0]["commit"]["committer"]["date"]
                created = json.loads(commits_html)[-1]["commit"]["committer"]["date"]
                pair = Pair(created=created, last_updated=last_updated, lg1=lg1.strip(), lg2=lg2.strip(), direction=direction, repo=repo_name, stems=stems)
                print(json.dumps(pair, default=lambda o: dict(o)))
                pairs.append(pair)
                time.sleep(3) #if you change this value you will get blocked likely

            except (IndexError, TypeError):
                pass #this happens if there is a weird entry in the repo

if __name__ == "__main__":
    with open('pairs.json', 'a') as f:
        json_string = json.dumps([dict(ob) for ob in pairs])
