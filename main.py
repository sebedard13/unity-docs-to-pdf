import json
import time
from bs4 import BeautifulSoup
from dominate import document
from dominate.tags import *
import subprocess

import parser_correct

folder = "Manual/"


def do_page(current_data, main_body, heading, deep=0):
    if "link" in current_data.keys():
        link = current_data["link"]
        if link is None or link == "null":
            # Some link does not have a html file but are a parent to multiples children.
            # Create a section with only the title inside
            current_section = BeautifulSoup("<div><h1>" + current_data["title"] + "</h1></div>", features="lxml").find(
                "div")
            current_section.attrs["class"] = "section"

            current_section = parser_correct.title(current_section, deep, heading)

            main_body.append(current_section)
            pass
        else:
            filename = folder + link + ".html"

            with open(filename, encoding="utf-8") as fp:
                d = BeautifulSoup(fp, features="lxml")

            current_section = d.select(".content-block .section")[0]

            current_section = parser_correct.bad_elements(current_section)
            current_section = parser_correct.tooltip(current_section)
            current_section = parser_correct.links(current_section, link)
            current_section = parser_correct.external_links(current_section)
            current_section = parser_correct.title(current_section, deep, heading, link)
            current_section = parser_correct.img_svg(current_section)
            current_section = parser_correct.code(current_section)

            main_body.append(current_section)

    if "children" in current_data.keys():
        children = current_data["children"]
        if children is not None:
            i = 0
            for child in children:
                i = i + 1
                newheading = heading + "." + str(i)
                do_page(child, main_body, newheading, deep + 1)


def generate_html(json_file, out_filename="out", starts=0, ends=-1):
    f = open(json_file)
    print("Load table of content")
    data = json.load(f)

    with document() as doc:
        main()

    with open('out/' + out_filename + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render())

    with open('out/' + out_filename + '.html', encoding="utf-8") as fp:
        appendHtml = BeautifulSoup(fp, features="lxml")

    mainBody = appendHtml.select("main")[0]

    if ends<starts or ends> len(data["children"]):
        ends = len(data["children"])

    print("Begin Html")
    for i in range(starts, ends):
        heading = str(i + 1)
        do_page(data["children"][i], mainBody, heading, 0)
    print("Html Done")

    with document(title=data["title"]) as doc:
        doc.head.add_raw_string("<link rel='stylesheet' href='main.css'>")
        doc.body.add_raw_string(str(mainBody))

    with open('out/' + out_filename + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render(pretty=False))
    print("Html Written")


def correct_bad_links(filename_in, filename_out=""):
    if filename_out=="":
        filename_out = filename_in

    with open("out/" + filename_in + ".html", encoding="utf-8") as fp:
        html = BeautifulSoup(fp, features="html.parser")

    id_map = []
    for elementId in html.select("*[id]"):
        if elementId.attrs["id"] not in id_map:
            id_map.append(elementId.attrs["id"])

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
            elif href.startswith("mailto:"):
                pass
            else:
                # I guess a file to found or a link to a page
                bad_href.append(href)

    for href in bad_href:
        for bad_a in html.select("a[href='" + href + "']"):
            bad_a.name = "span"
            bad_a.attrs["class"] = "bad-link"
            del bad_a["href"]

    with open('out/' + filename_out + '.html', 'w', encoding="utf-8") as f:
        f.write(str(html))
    print(len(bad_href), "Bad links corrected")


def generate_pdf(filename):
    print("PDF Begin, Resolving links may take a really long time like 20 minutes on a i7-9750H")
    command_args = [
        "-n",
        "--print-media-type",
        "--disable-toc-back-links",
        # "--disable-internal-links",
        # "--disable-external-links",
        "--enable-local-file-access",
        "--encoding utf-8"
    ]
    start_time = time.time()

    command = 'wkhtmltopdf out/' + filename + '.html'

    for arg in command_args:
        command = command + " " + arg
    command = command + ' out/' + filename + '.pdf'

    process = subprocess.Popen(
        command,
        shell=False)
    process.wait()
    print("PDF end in %s seconds" % (time.time() - start_time))


if __name__ == '__main__':
    filename = "out_test"
    generate_html(folder + "docdata/" + 'toc.json', filename, 0, -1)

    # You can look a test_link.py before to list them if you want
    # but most of them are 404
    correct_bad_links(filename)

    generate_pdf(filename)
