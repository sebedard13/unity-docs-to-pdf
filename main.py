import json
import os
import string
from bs4 import BeautifulSoup
from dominate import document
from dominate.tags import *
import subprocess

folder = "Manual/"


def changeLink(currentSection):
    for link in currentSection.select("a[href$='.html']"):
        href = link.attrs["href"]
        if href:
            if href.__contains__(".html"):
                id_section = os.path.basename(href)
                id_section = id_section.replace(".html", "")
                link.attrs["href"] = "#" + id_section

    return currentSection


def correctTitle(currentSection, deep=0, heading="", id=""):
    selections = currentSection.select("h2, h3, h4, h5, h6")
    for h in selections:
        body = BeautifulSoup("<p></p>", features="lxml")
        body.p.attrs['class'] = h.name
        body.p.contents = h.contents
        h.replaceWith(body.p)

    currentSection = BeautifulSoup(str(currentSection), features="lxml")

    selectionsh1 = currentSection.select("h1")
    idDone = False
    tag = "h" + str(deep + 1)
    for h in selectionsh1:
        body = BeautifulSoup("<" + tag + "></" + tag + ">", features="lxml")
        curr = body.find(tag)
        if not idDone:
            curr.attrs["id"] = id
            curr.contents = h.contents
            curr.string = heading + " " + curr.text
            tag = "h" + str(deep + 2)
            idDone = True
        else:
            curr.contents = h.contents
        h.replaceWith(curr)

    return currentSection.select(".section")[0]


def correctImgSVG(currentSection):
    for img in currentSection.select("img[src$='.svg']"):
        body = BeautifulSoup("<embed></embed>", features="lxml")
        curr = body.find("embed")
        if "alt" in img.attrs.keys():
            curr.attrs["title"] = img.attrs["alt"]
        if "src" in img.attrs.keys():
            src = img.attrs["src"]
            curr.attrs["src"] = src
            src = src.replace("../", "")
            with open(src, encoding="utf-8") as fp:
                svgFile = BeautifulSoup(fp, features="lxml")
            svgTag = svgFile.find("svg")
            if "width" in svgTag.attrs.keys():
                width_str = svgTag.attrs["width"]
                tr_table = str.maketrans({c: None for c in string.ascii_letters})
                width_str = width_str.translate(tr_table)
                curr.attrs["width"] = width_str + "px"
                if float(width_str)>1200:
                    # curr.attrs["width"] = str(1200)+ "px"
                    scale_v =1200/float(width_str)
                    curr.attrs["style"] = "transform: scale("+str(scale_v)+");"

            if "height" in svgTag.attrs.keys():
                curr.attrs["height"] = svgTag.attrs["height"]+"px"

        img.replaceWith(curr)

    return currentSection
def doPage(currentData, mainBody, heading, deep=0):
    if "link" in currentData.keys():
        l = currentData["link"]
        if l is None or l == "null":
            return

    filename = folder + currentData["link"] + ".html"

    with open(filename, encoding="utf-8") as fp:
        d = BeautifulSoup(fp, features="lxml")

    currentSection = d.select(".content-block .section")[0]
    for bad in currentSection.select(
            ".breadcrumbs, .mb20, #_leavefeedback, .clear, #_content, a:empty, .tooltiptext br"):
        bad.decompose()

    currentSection = changeLink(currentSection)
    currentSection = correctTitle(currentSection, deep, heading, currentData["link"])
    currentSection = correctImgSVG(currentSection)

    mainBody.append(currentSection)

    if "children" in currentData.keys():
        children = currentData["children"]
        if (children is not None):
            i = 0
            for child in children:
                i = i + 1
                newheading = heading + "." + str(i)
                doPage(child, mainBody, newheading, deep + 1)


def main_fn(jsonFile, outFileName="out"):
    # Opening JSON file
    f = open(jsonFile)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    with document() as doc:
        main()

    with open('out/' + outFileName + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render())

    with open('out/' + outFileName + '.html', encoding="utf-8") as fp:
        appendHtml = BeautifulSoup(fp, features="lxml")

    mainBody = appendHtml.select("main")[0]

    i = 0
    for child in data["children"]:
        i = i + 1
        heading = str(i)
        doPage(child, mainBody, heading, 0)
    print("Html Done")

    with document(title=data["title"]) as doc:
        doc.head.add_raw_string("<link rel='stylesheet' href='main.css'>")
        doc.body.add_raw_string(str(mainBody))

    with open('out/' + outFileName + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render(pretty=False))
    print("Html Written")


if __name__ == '__main__':
    out = "out"
    main_fn(folder + "docdata/" + 'toc.json', out)

    process = subprocess.Popen(
        'wkhtmltopdf out/' + out + '.html --disable-internal-links -n --print-media-type --disable-toc-back-links --enable-local-file-access --encoding utf-8 out/' + out + '.pdf',
        shell=False)
    process.wait()
    print(process.returncode)
