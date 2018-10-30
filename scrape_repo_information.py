import urllib.request
import pdb
import xml.etree.ElementTree as xml
import argparse, urllib.request
import json
import collections
import time
import urllib
import os
"""
Script to scrape text from GitHub and into JSON format for all language pairs in Apertium.
Stem counter by sushain
"""
if "GITHUB_CLIENT_ID" in os.environ:
    CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
else:
    CLIENT_ID = ""
    print("There doesn't seem to be a GitHub Client ID; the scraping process may not be fast")
if "GITHUB_SECRET_CLIENT_ID" in os.environ:
    CLIENT_SECRET = os.environ["GITHUB_SECRET_CLIENT_ID"]
else:
    CLIENT_SECRET = ""
    print("There doesn't seem to be a GitHub Client Secret; the scraping process may not be fast")


pairs = []
Pair = collections.namedtuple("Pair", "lg1 lg2 last_updated created direction repo stems")
types = ["trunk", "nursery", "incubator", "staging"]

params = urllib.parse.urlencode(dict({"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}))

def print_info(uri):
    try:
        dictX = str((urllib.request.urlopen(uri)).read(), "utf-8")
        tree = xml.fromstring(dictX)
    except:
        return -1 # FIXME: error handling

    return len(tree.findall("*[@id='main']/e//l"))

def main():
    for repo_name in types:
        types_html_url = "https://api.github.com/repos/apertium/apertium-%s/contents?" % repo_name
        types_html_data = urllib.request.urlopen(types_html_url + params)
        types_html = json.loads(types_html_data.read())
        for type_content in types_html:
            if "apertium" in type_content["name"] and (type_content["name"].count("-") == 2):
                direction = ""
                lang_pair_name = type_content["name"]

                #getting names
                _, lg1, lg2 = lang_pair_name.split("-")

                #getting into repository
                link = "https://api.github.com/repos/apertium/%s/contents?" % lang_pair_name
                repo_json = json.loads(urllib.request.urlopen(link + params).read())
                for el in repo_json:
                    if el["name"] == "modes.xml":
                        download_url = el["download_url"]
                        html_for_blob_utf_8 = str((urllib.request.urlopen(download_url)).read(), "utf-8")
                        tree = xml.fromstring(html_for_blob_utf_8)
                        for mode in tree:
                            if lg1+"-"+lg2 == mode.attrib["name"] and "<" not in direction:
                                direction += "<"
                            if lg2+"-"+lg1 in mode.attrib["name"] and ">" not in direction:
                                direction += ">"

                    elif el["name"] == "apertium-%s.%s.dix" % ((lg1+"-"+lg2), (lg1+"-"+lg2)):
                        stems = print_info(el["download_url"])

                    if direction == "><":
                        direction = "<>"

                commits_link = "https://api.github.com/repos/apertium/%s/commits?" % lang_pair_name
                commits_html = urllib.request.urlopen(commits_link + params).read()
                commit_json = json.loads(commits_html)
                last_updated = commit_json[0]["commit"]["committer"]["date"]
                created = commit_json[-1]["commit"]["committer"]["date"]
                pair = Pair(created=created, last_updated=last_updated, lg1=lg1.strip(), lg2=lg2.strip(), direction=direction, repo=repo_name, stems=stems)
                print(json.dumps(pair._asdict(), default=lambda o: dict(o)))
                pairs.append(pair)

    with open("pairs.json", "a") as f:
        json_string = json.dumps([ob._asdict() for ob in pairs])
        f.write(json_string)

if __name__ == "__main__":
    main()
