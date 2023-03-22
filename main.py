import json
import os
import time

from bs4 import BeautifulSoup
from dominate import document
from dominate.tags import *
import subprocess

folder = "Manual/"


def changeLink(currentSection, currentSectionId):
    # all link ending with href
    for link in currentSection.select("a[href^='#']"):
        href = link.attrs["href"]
        id_section = os.path.basename(href)
        id_section = id_section.replace("#", "")
        link.attrs["href"] = "#" + currentSectionId+"-"+id_section

    # all link ending with href
    for link in currentSection.select("a[href$='.html']"):
        href = link.attrs["href"]
        if href.__contains__("https") or href.__contains__("http"):
            continue

        if href.__contains__("/"):
            continue
        id_section = os.path.basename(href)
        id_section = id_section.replace(".html", "")
        link.attrs["href"] = "#" + id_section

    for link in currentSection.select("a[href*='.html#']"):
        href = link.attrs["href"]
        if href.__contains__("https") or href.__contains__("http"):
            continue

        if href.__contains__("/"):
            continue

        id_section = os.path.basename(href)
        id_section = id_section.replace(".html#", "-")
        link.attrs["href"] = "#" + id_section

    for objId in currentSection.select("*[id]"):
        id = objId.attrs["id"]
        objId.attrs["id"] = currentSectionId + "-" + id

    for objAName in currentSection.select("a[name]"):
        name = objAName.attrs["name"]
        objAName.attrs["id"] = currentSectionId + "-" + name
        del objAName.attrs["name"]

    for aEmpty in currentSection.select("p a:empty:only-child"):
        parent = aEmpty.parent
        parent.replaceWith(aEmpty)

    for hWithPreviousLink in currentSection.select("a:empty + h1, a:empty + h2, a:empty + h3, a:empty + h4, a:empty + h5, a:empty + h6"):
        sibling = hWithPreviousLink.find_previous_sibling("a")
        hWithPreviousLink["id"] = sibling.attrs["id"]
        sibling.decompose()

    for aEmpty in currentSection.select("a:empty"):
        aEmpty.attrs["class"]="empty-link"
        aEmpty.string = "[L]"

    return currentSection


def correctTitle(currentSection, deep=0, heading="", id=""):
    selections = currentSection.select("h2, h3, h4, h5, h6")
    for h in selections:
        body = BeautifulSoup("<p></p>", features="lxml")
        body.p.attrs['class'] = h.name
        if "id" in h.attrs.keys():
            body.p.attrs['id'] = h.attrs["id"]
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
        src = img.attrs["src"].replace("../","")
        output = src.replace(".svg", ".png")
        if not os.path.exists(output):
            process = subprocess.Popen(
                "inkscape -z -f "+src+" -e "+output, shell=False)
            process.wait()
        img.attrs["src"] = "../"+output

    return currentSection


def correctToolTip(currentSection):
    for toolTip in currentSection.select(".tooltiptext"):
        span = BeautifulSoup("<sup></sup>", features="lxml").find("sup")
        span.attrs["class"] = "indice"
        select = toolTip.select("a")
        for aElement in select:
            if "href" in aElement.attrs.keys() and aElement.attrs["href"].__contains__("Glossary.html"):
                a = BeautifulSoup("<a>[G]</a>", features="lxml").find("a")
                a.attrs = aElement.attrs
                span.append(a)
            else:
                a = BeautifulSoup("<a>[M]</a>", features="lxml").find("a")
                a.attrs = aElement.attrs
                span.append(a)
        toolTip.replaceWith(span)

    return currentSection


def correctCode(currentSection):
    for code in currentSection.select("pre code"):
        pre = code.parent
        if("class" in  pre.attrs.keys()):
            pre.attrs["class"].append("pre-code")
        else:
            pre.attrs["class"] = "pre-code"

    return currentSection


def correctExternalLink(currentSection):
    for externalA in currentSection.select("a:not([href^= '#'])"):
        externalA.attrs["target"] = "_blank"
        span = BeautifulSoup("<span></span>", features="lxml").find("span")

        sup = BeautifulSoup("<sup></sup>", features="lxml").find("sup")
        sup.string = "[E]"
        sup.attrs["class"] = "indice"

        a = BeautifulSoup(str(externalA), features="lxml").find("a")
        span.append(a)
        span.append(sup)
        externalA.replaceWith(span)

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
            ".breadcrumbs, .mb20, #_leavefeedback, .clear, #_content, .tooltiptext br"):
        bad.decompose()

    currentSection = correctToolTip(currentSection)
    currentSection = changeLink(currentSection, currentData["link"])
    currentSection = correctExternalLink(currentSection)
    currentSection = correctTitle(currentSection, deep, heading, currentData["link"])
    currentSection = correctImgSVG(currentSection)
    currentSection = correctCode(currentSection)


    mainBody.append(currentSection)

    if "children" in currentData.keys():
        children = currentData["children"]
        if (children is not None):
            i = 0
            for child in children:
                i = i + 1
                newheading = heading + "." + str(i)
                doPage(child, mainBody, newheading, deep + 1)


def generate_html(jsonFile, outFileName="out"):
    f = open(jsonFile)
    data = json.load(f)

    with document() as doc:
        main()

    with open('out/' + outFileName + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render())

    with open('out/' + outFileName + '.html', encoding="utf-8") as fp:
        appendHtml = BeautifulSoup(fp, features="lxml")

    mainBody = appendHtml.select("main")[0]

    for i in range(0, len(data["children"])):
    # for i in range(0, 3):
        heading = str(i + 1)
        doPage(data["children"][i], mainBody, heading, 0)

    # For glossary when doing part of docs
    # heading = str(len(data["children"]))
    # doPage(data["children"][len(data["children"])-1], mainBody, heading, 0)
    print("Html Done")

    with document(title=data["title"]) as doc:
        doc.head.add_raw_string("<link rel='stylesheet' href='main.css'>")
        doc.body.add_raw_string(str(mainBody))

    with open('out/' + outFileName + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render(pretty=False))
    print("Html Written")

if __name__ == '__main__':
    out = "out"
    generate_html(folder + "docdata/" + 'toc.json', out)

    print("PDF Begin, Resolving links may take a really long time like 20 minutes on a i7-9750H")
    start_time = time.time()
    process = subprocess.Popen(
        'wkhtmltopdf out/' + out + '.html -n --print-media-type --disable-toc-back-links --enable-local-file-access --encoding utf-8 out/' + out + '.pdf',
        shell=False)
    process.wait()
    print("PDF end in %s seconds" % (time.time() - start_time))
