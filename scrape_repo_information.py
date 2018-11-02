import collections
import json
import os
import time
import urllib
import urllib.request
import xml.etree.ElementTree as xml
import sys
import time
"""
Script to scrape text from GitHub and into JSON format for all language pairs in Apertium.
Stem counter by sushain
One entry in the JSON file would be
{"lg1": "afr", "lg2": "nld", "last_updated": "2018-07-21T23:55:22Z", "created": "2012-02-08T15:12:04Z", "direction": "<>", "repo": "trunk", "stems": 6269}
"""

if "GITHUB_CLIENT_ID" in os.environ:
    CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
else:
    CLIENT_ID = None
    print("Set Github Client Id in ENV variable to 'GITHUB_CLIENT_ID' There doesn't seem to be a GitHub Client ID; Please set an enviornment variable of GITHUB_CLINT_ID to your client id. the scraping process may not be fast get one here https://github.com/settings/applications/new")

if "GITHUB_SECRET_CLIENT_ID" in os.environ:
    CLIENT_SECRET = os.environ["GITHUB_SECRET_CLIENT_ID"]
else:
    CLIENT_SECRET = None
    print("Set Github Client secret Id in ENV variable to 'GITHUB_SECRET_CLIENT_ID' There doesn't seem to be a GitHub Client Secret; Please set an enviornment variable of CLIENT_SECRET to your client secret id. the scraping process may not be fast get one here https://github.com/settings/applications/new")

Pair = collections.namedtuple("Pair", "lg1 lg2 last_updated created direction repo stems")
types = ["trunk", "incubator", "nursery", "staging"]

def get_bidix_stem_count(uri):
    try:
        dix_content = urllib.request.urlopen(uri).read().decode()
        tree = xml.fromstring(dix_content)
    except:
        return -1 # FIXME: error handling

    return len(tree.findall("*[@id='main']/e//l"))

def main():
    pairs = []
    params = urllib.parse.urlencode(dict({"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}))
    for repo_name in types:
        types_data_url = "https://api.github.com/repos/apertium/apertium-%s/contents?" % repo_name
        types_data_data = urllib.request.urlopen(types_data_url + params)
        types_data = json.loads(types_data_data.read())
        for type_content in types_data:
            lang_pair_name = type_content["name"]
            if "apertium" in lang_pair_name and (lang_pair_name.count("-") == 2):
                direction = ""

                #getting names
                _, lg1, lg2 = lang_pair_name.split("-")

                #getting into repository
                if lg1 == lg2:
                    continue

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
                        stems = get_bidix_stem_count(el["download_url"])

                    if direction == "><":
                        direction = "<>"

                first_page_commits_link = "https://api.github.com/repos/apertium/%s/commits?" % lang_pair_name
                first_page_commits_resp = urllib.request.urlopen(first_page_commits_link + params)
                first_page_commits_data = first_page_commits_resp.read()
                first_page_commit_json = json.loads(first_page_commits_data)

                # '<https://api.github.com/repositories/124326860/commits?client_id=f55561171db254c8481c&client_secret=59fa2eb87e77f2f841cc4fba06fb6185121d1b5e&page=2>; rel="next", <https://api.github.com/repositories/124326860/commits?client_id=f55561171db254c8481c&client_secret=59fa2eb87e77f2f841cc4fba06fb6185121d1b5e&page=21>; rel="last"'

                if first_page_commits_resp.info().get("Link") is not None:
                    number_of_pages = first_page_commits_resp.info().get("Link").split(",")[1].split("page=")[1].split(">")[0]
                else:
                    number_of_pages = 1

                last_page_commits_link = "https://api.github.com/repos/apertium/%s/commits?page=%s&" % (lang_pair_name, number_of_pages)
                last_page_commits_data = urllib.request.urlopen(last_page_commits_link + params).read()

                last_page_commit_json = json.loads(last_page_commits_data)
                last_updated = first_page_commit_json[0]["commit"]["committer"]["date"]
                created = last_page_commit_json[-1]["commit"]["committer"]["date"]

                pair = Pair(created=created, last_updated=last_updated, lg1=lg1, lg2=lg2, direction=direction, repo=repo_name, stems=stems)
                print(json.dumps(pair._asdict(), default=lambda o: dict(o)))
                pairs.append(pair)

                if CLIENT_SECRET == None or CLIENT_ID == None:
                    time.sleep(5)

    output_file = sys.argv[1] if len(sys.argv) > 1 else "pairs.json"
    with open(output_file, "w") as f:
        json.dump([ob._asdict() for ob in pairs], f)


if __name__ == "__main__":
    main()
