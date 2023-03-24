import os

import requests as requests
from bs4 import BeautifulSoup


def check_id(html: BeautifulSoup) -> tuple[list[str], list[str]]:
    id_map = []
    id_map_doublon = []
    for elementId in html.select("*[id]"):
        if elementId.attrs["id"] in id_map:
            id_map_doublon.append(elementId.attrs["id"])
        else:
            id_map.append(elementId.attrs["id"])
    return id_map, id_map_doublon


def check_links(html, folder_path="", id_map=None) -> list[str]:
    if id_map is None:
        id_map = []

    bad_href = []
    done_href = []
    for a_element in html.select("a[href]"):
        href = a_element.attrs["href"]

        if href not in done_href:
            done_href.append(href)
            if href.startswith("#"):
                if not href.removeprefix("#") in id_map:
                    bad_href.append(href)

            elif href.startswith("http"):
                pass
                # try:
                #     r = requests.head(href)
                #     if 400 <= r.status_code < 500:
                #         bad_href.append(href)
                # except requests.ConnectionError:
                #     bad_href.append(href)
                # pass
            elif href.startswith("mailto:"):
                pass
            else:
                # I guess a file to found
                bad_href.append(href)

    return bad_href


if __name__ == '__main__':

    folder_path = "out/"
    filename = folder_path + "out.html"

    with open(filename, encoding="utf-8") as fp:
        html = BeautifulSoup(fp, features="html.parser")

    id_map, id_map_doublon = check_id(html)


    for id_doublon in id_map_doublon:
        print("Id doublon", id_doublon)

    bad_href = check_links(html, id_map=id_map, folder_path=folder_path)

    bad_href.sort()

    for href in bad_href:
        print("Bad link", href)

    print("Doublons", len(id_map_doublon), "Bad links", len(bad_href))
