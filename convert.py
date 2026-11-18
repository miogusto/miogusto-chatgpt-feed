#!/usr/bin/env python3
"""Ticimax Google-Merchant (Atom) XML  ->  OpenAI/ChatGPT urun akisi (CSV.GZ).

Kullanim:  XML_URL=... python convert.py public/urunler.csv.gz
"""
import csv
import gzip
import html
import io
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

MIN_ROWS = 500          # bundan az satir cikarsa yayin YAPILMAZ (bozuk XML korumasi)
DESC_MAX = 4500
SELLER = "Mio Gusto"
COUNTRY = "TR"
CURRENCY = "TRY"

COLUMNS = [
    "item_id", "title", "description", "url", "brand", "seller_name",
    "image_url", "availability", "price", "sale_price", "group_id",
    "listing_has_variations", "variant_dict", "condition", "product_category",
    "color", "size", "gender", "age_group", "additional_image_urls",
    "target_countries", "store_country", "is_eligible_search",
]


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self.parts.append(" ")


def plain(text):
    p = _Text()
    p.feed(html.unescape(text) if "&lt;" in text else text)
    out = re.sub(r"\s+", " ", "".join(p.parts)).strip()
    if len(out) > DESC_MAX:
        out = out[:DESC_MAX].rsplit(" ", 1)[0]
    return out


def money(s):
    m = re.search(r"([\d.,]+)", s or "")
    if not m:
        return ""
    n = m.group(1)
    if "," in n and "." in n:
        n = n.replace(".", "").replace(",", ".")
    elif "," in n:
        n = n.replace(",", ".")
    try:
        v = float(n)
    except ValueError:
        return ""
    return f"{v:.2f} {CURRENCY}" if v > 0 else ""


def local(tag):
    return tag.rsplit("}", 1)[-1].split(":")[-1]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mio-gusto-feed/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    url = os.environ["XML_URL"]
    out_path = sys.argv[1] if len(sys.argv) > 1 else "public/urunler.csv.gz"
    root = ET.fromstring(fetch(url))

    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)

    seen, n = set(), 0
    for e in root:
        if local(e.tag) != "entry":
            continue
        f, many = {}, {}
        for c in e:
            k = local(c.tag)
            v = (c.text or "").strip()
            f.setdefault(k, v)
            many.setdefault(k, []).append(v)

        item_id = f.get("id", "")
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)

        price = money(f.get("price"))
        if not price or not f.get("link") or not f.get("image_link"):
            continue
        sale = money(f.get("sale_price"))
        if sale and float(sale.split()[0]) >= float(price.split()[0]):
            sale = ""

        av = (f.get("availability") or "").lower().replace(" ", "_")
        availability = av if av in ("in_stock", "out_of_stock", "backorder") else (
            "pre_order" if av == "preorder" else "unknown")

        size = ""
        for a in many.get("additional_variant_attribute", []):
            s = re.sub(r"\s+", " ", a).strip()
            if re.match(r"(?i)^numara\b", s):
                size = re.sub(r"(?i)^numara\s*", "", s)

        color = f.get("color", "")
        vd = {}
        if color:
            vd["color"] = color
        if size:
            vd["size"] = size
        group = f.get("item_group_id", "")
        has_var = bool(vd) and bool(group) and group != item_id

        title = f.get("title", "") + (f" - Numara {size}" if size else "")
        extra = ",".join(u.replace(",", "%2C") for u in many.get("additional_image_link", []) if u)
        cat = re.sub(r"\s*>\s*", " > ", f.get("product_type", ""))

        w.writerow([
            item_id, title, plain(f.get("description", "")), f["link"],
            f.get("brand") or "MIO GUSTO", SELLER, f["image_link"], availability,
            price, sale, group if has_var else "", "true" if has_var else "",
            json.dumps(vd, ensure_ascii=False) if has_var else "",
            f.get("condition") or "new", cat, color, size, "female", "adult",
            extra, COUNTRY, COUNTRY, "true",
        ])
        n += 1

    if n < MIN_ROWS:
        sys.exit(f"HATA: yalnizca {n} urun satiri cikti (en az {MIN_ROWS} bekleniyor). Yayin iptal.")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(buf.getvalue().encode("utf-8"))
    print(f"{n} satir yazildi -> {out_path}")


if __name__ == "__main__":
    main()
