import os

from bs4 import BeautifulSoup
import subprocess
from pathlib import Path

def bad_elements(current_section):
    for bad in current_section.select(
            ".breadcrumbs, .mb20, #_leavefeedback, .clear, #_content, .tooltiptext br"):
        bad.decompose()

    return current_section

def links(current_section, current_section_id):
    # all link ending with href
    for link in current_section.select("a[href^='#']"):
        href = link.attrs["href"]
        id_section = os.path.basename(href)
        id_section = id_section.replace("#", "")
        link.attrs["href"] = "#" + current_section_id + "-" + id_section

    # all link ending with href
    for link in current_section.select("a[href$='.html']"):
        href = link.attrs["href"]
        if "https" in href or "http" in href:
            continue

        if "../ScriptReference" in href:
            href = href.replace("../ScriptReference", "https://docs.unity3d.com/ScriptReference")
            link.attrs["href"] = href
            continue

        if "../Manual" in href:
            href = href.replace("../Manual", "https://docs.unity3d.com/ScriptReference")
            link.attrs["href"] = href
            continue

        if href.startswith("/") and href.count("/") == 1:
            href = href.replace("/", "")

        if "/" in href:
            continue

        id_section = os.path.basename(href)
        id_section = id_section.replace(".html", "")
        link.attrs["href"] = "#" + id_section

    for link in current_section.select("a[href*='.html#']"):
        href = link.attrs["href"]
        if "https" in href or "http" in href:
            continue

        if "/" in href:
            continue

        id_section = os.path.basename(href)
        id_section = id_section.replace(".html#", "-")
        link.attrs["href"] = "#" + id_section

    for link in current_section.select("a[href^='../']"):
        href = link.attrs["href"]
        href = href.replace("../", "https://docs.unity3d.com/")
        link.attrs["href"] = href
        continue

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

def title(current_section, deep=0, heading="", id_section=""):
    if len(current_section.select("h1")) == 0:
        first_h2 = current_section.select("h2")[0]
        first_h2.name = "h1"

    selections = current_section.select("h2, h3, h4, h5, h6")
    for h in selections:
        body = BeautifulSoup("<p></p>", features="html.parser")
        body.p.attrs['class'] = h.name
        if "id" in h.attrs.keys():
            body.p.attrs['id'] = h.attrs["id"]
        body.p.contents = h.contents
        h.replaceWith(body.p)

    current_section = BeautifulSoup(str(current_section), features="html.parser")

    selectionsh1 = current_section.select("h1")
    idDone = False
    tag = "h" + str(deep + 1)
    for h in selectionsh1:
        body = BeautifulSoup("<" + tag + "></" + tag + ">", features="html.parser")
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

def img_svg(current_section):
    for img in current_section.select("img[src$='.svg']"):
        src = img.attrs["src"].replace("../", "")
        output = Path(src.replace(".svg", ".png"))
        output = Path("svg_to_png") / Path(*output.parts[1:])
        if not os.path.exists(output):
            Path(*output.parts[:-1]).mkdir(parents=True, exist_ok=True)
            process = subprocess.Popen(
                "inkscape " + src + " -o " + str(output), shell=False)
            process.wait()
        img.attrs["src"] = "../" + str(output)

    return current_section

def tooltip(current_section):
    for toolTip in current_section.select(".tooltiptext"):
        span = BeautifulSoup("<sup></sup>", features="html.parser").find("sup")
        span.attrs["class"] = "indice"
        select = toolTip.select("a")
        for aElement in select:
            if "href" in aElement.attrs.keys() and "Glossary.html" in aElement.attrs["href"]:
                a = BeautifulSoup("<a>[G]</a>", features="html.parser").find("a")
                a.attrs = aElement.attrs
                span.append(a)
            else:
                a = BeautifulSoup("<a>[M]</a>", features="html.parser").find("a")
                a.attrs = aElement.attrs
                span.append(a)
        toolTip.replaceWith(span)

    return current_section

def code(current_section):
    for code in current_section.select("pre code"):
        pre = code.parent
        if "class" in pre.attrs.keys():
            pre.attrs["class"].append("pre-code")
        else:
            pre.attrs["class"] = "pre-code"

    return current_section

def external_links(current_section):
    for externalA in current_section.select("a:not([href^= '#'])"):
        externalA.attrs["target"] = "_blank"
        span = BeautifulSoup("<span></span>", features="html.parser").find("span")

        sup = BeautifulSoup("<sup></sup>", features="html.parser").find("sup")
        sup.string = "[E]"
        sup.attrs["class"] = "indice"

        a = BeautifulSoup(str(externalA), features="html.parser").find("a")
        span.append(a)
        span.append(sup)
        externalA.replaceWith(span)

    return current_section
