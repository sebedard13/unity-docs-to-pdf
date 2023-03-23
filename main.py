import json
import os
import time

from bs4 import BeautifulSoup
from dominate import document
from dominate.tags import *
import subprocess

folder = "Manual/"


def change_link(current_section, current_section_id):
    # all link ending with href
    for link in current_section.select("a[href^='#']"):
        href = link.attrs["href"]
        id_section = os.path.basename(href)
        id_section = id_section.replace("#", "")
        link.attrs["href"] = "#" + current_section_id + "-" + id_section

    # all link ending with href
    for link in current_section.select("a[href$='.html']"):
        href = link.attrs["href"]
        if href in "https" or href in "http":
            continue

        if href in "/":
            continue
        id_section = os.path.basename(href)
        id_section = id_section.replace(".html", "")
        link.attrs["href"] = "#" + id_section

    for link in current_section.select("a[href*='.html#']"):
        href = link.attrs["href"]
        if href in "https" or href in "http":
            continue

        if href in "/":
            continue

        id_section = os.path.basename(href)
        id_section = id_section.replace(".html#", "-")
        link.attrs["href"] = "#" + id_section

    for objId in current_section.select("*[id]"):
        id_attr = objId.attrs["id"]
        objId.attrs["id"] = current_section_id + "-" + id_attr

    for objAName in current_section.select("a[name]"):
        name = objAName.attrs["name"]
        objAName.attrs["id"] = current_section_id + "-" + name
        del objAName.attrs["name"]

    for aEmpty in current_section.select("p a:empty:only-child"):
        parent = aEmpty.parent
        parent.replaceWith(aEmpty)

    for hWithPreviousLink in current_section.select(
            "a:empty + h1, a:empty + h2, a:empty + h3, a:empty + h4, a:empty + h5, a:empty + h6"):
        sibling = hWithPreviousLink.find_previous_sibling("a")
        hWithPreviousLink["id"] = sibling.attrs["id"]
        sibling.decompose()

    for aEmpty in current_section.select("a:empty"):
        aEmpty.attrs["class"] = "empty-link"
        aEmpty.string = "[L]"

    return current_section


def correct_title(current_section, deep=0, heading="", id_section=""):
    selections = current_section.select("h2, h3, h4, h5, h6")
    for h in selections:
        body = BeautifulSoup("<p></p>", features="lxml")
        body.p.attrs['class'] = h.name
        if "id" in h.attrs.keys():
            body.p.attrs['id'] = h.attrs["id"]
        body.p.contents = h.contents
        h.replaceWith(body.p)

    current_section = BeautifulSoup(str(current_section), features="lxml")

    selectionsh1 = current_section.select("h1")
    idDone = False
    tag = "h" + str(deep + 1)
    for h in selectionsh1:
        body = BeautifulSoup("<" + tag + "></" + tag + ">", features="lxml")
        curr = body.find(tag)
        if not idDone:
            curr.attrs["id"] = id_section
            curr.contents = h.contents
            curr.string = heading + " " + curr.text
            tag = "h" + str(deep + 2)
            idDone = True
        else:
            curr.contents = h.contents
        h.replaceWith(curr)

    return current_section.select(".section")[0]


def correct_img_svg(current_section):
    for img in current_section.select("img[src$='.svg']"):
        src = img.attrs["src"].replace("../", "")
        output = src.replace(".svg", ".png")
        if not os.path.exists(output):
            process = subprocess.Popen(
                "inkscape -z -f " + src + " -e " + output, shell=False)
            process.wait()
        img.attrs["src"] = "../" + output

    return current_section


def correct_tool_tip(current_section):
    for toolTip in current_section.select(".tooltiptext"):
        span = BeautifulSoup("<sup></sup>", features="lxml").find("sup")
        span.attrs["class"] = "indice"
        select = toolTip.select("a")
        for aElement in select:
            if "href" in aElement.attrs.keys() and aElement.attrs["href"] in "Glossary.html":
                a = BeautifulSoup("<a>[G]</a>", features="lxml").find("a")
                a.attrs = aElement.attrs
                span.append(a)
            else:
                a = BeautifulSoup("<a>[M]</a>", features="lxml").find("a")
                a.attrs = aElement.attrs
                span.append(a)
        toolTip.replaceWith(span)

    return current_section


def correct_code(current_section):
    for code in current_section.select("pre code"):
        pre = code.parent
        if "class" in pre.attrs.keys():
            pre.attrs["class"].append("pre-code")
        else:
            pre.attrs["class"] = "pre-code"

    return current_section


def correct_external_link(current_section):
    for externalA in current_section.select("a:not([href^= '#'])"):
        externalA.attrs["target"] = "_blank"
        span = BeautifulSoup("<span></span>", features="lxml").find("span")

        sup = BeautifulSoup("<sup></sup>", features="lxml").find("sup")
        sup.string = "[E]"
        sup.attrs["class"] = "indice"

        a = BeautifulSoup(str(externalA), features="lxml").find("a")
        span.append(a)
        span.append(sup)
        externalA.replaceWith(span)

    return current_section


def do_page(current_data, main_body, heading, deep=0):
    if "link" in current_data.keys():
        link = current_data["link"]
        if link is None or link == "null":
            return

    filename = folder + current_data["link"] + ".html"

    with open(filename, encoding="utf-8") as fp:
        d = BeautifulSoup(fp, features="lxml")

    currentSection = d.select(".content-block .section")[0]
    for bad in currentSection.select(
            ".breadcrumbs, .mb20, #_leavefeedback, .clear, #_content, .tooltiptext br"):
        bad.decompose()

    currentSection = correct_tool_tip(currentSection)
    currentSection = change_link(currentSection, current_data["link"])
    currentSection = correct_external_link(currentSection)
    currentSection = correct_title(currentSection, deep, heading, current_data["link"])
    currentSection = correct_img_svg(currentSection)
    currentSection = correct_code(currentSection)

    main_body.append(currentSection)

    if "children" in current_data.keys():
        children = current_data["children"]
        if children is not None:
            i = 0
            for child in children:
                i = i + 1
                newheading = heading + "." + str(i)
                do_page(child, main_body, newheading, deep + 1)


def generate_html(json_file, out_file_name="out"):
    f = open(json_file)
    data = json.load(f)

    with document() as doc:
        main()

    with open('out/' + out_file_name + '.html', 'w', encoding="utf-8") as f:
        f.write(doc.render())

    with open('out/' + out_file_name + '.html', encoding="utf-8") as fp:
        appendHtml = BeautifulSoup(fp, features="lxml")

    mainBody = appendHtml.select("main")[0]

    for i in range(0, len(data["children"])):
        # for i in range(0, 3):
        heading = str(i + 1)
        do_page(data["children"][i], mainBody, heading, 0)

    # For glossary when doing part of docs
    # heading = str(len(data["children"]))
    # doPage(data["children"][len(data["children"])-1], mainBody, heading, 0)
    print("Html Done")

    with document(title=data["title"]) as doc:
        doc.head.add_raw_string("<link rel='stylesheet' href='main.css'>")
        doc.body.add_raw_string(str(mainBody))

    with open('out/' + out_file_name + '.html', 'w', encoding="utf-8") as f:
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
