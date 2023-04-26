#!/usr/bin/env python3

from lxml import html
from dataclasses import dataclass
import pandoc
from models import db, Event, Place, CATEGORIES
from datetime import datetime, date
import locale
import os
import re
import requests
from settings import IMPORT_USERNAME, IMPORT_PASSWD, IMPORT_ARCHIVES

def md(html):
    # hacks hacks hacks
    html = html.replace(b' target="_blank"', b'')
    doc = pandoc.read(html, format='html')
    computed = pandoc.write(doc)
    computed = re.sub(r'\[([^\]]*)\]\{[^\}]*\}', r'\g<1>', computed)
    computed = re.sub(r'\[(.*)\]\{[^\}]*\}', r'\g<1>', computed)
    computed = computed.replace('\\\n', '\n').replace('\\"', '"').replace("\\'", "'")
    computed = re.sub(r'\n+', r'\n', computed)
    return computed

def process(category, token, suffix=''):
    print("#########", category, suffix)
    r = requests.get(f"https://agendainforme.htg0.com/admin/{category}.php?sid={token}{suffix}")
    page = r.text
    tree = html.fromstring(page)
    nb_columns = 0
    for line in tree.xpath("//tr"):
        recurring_info = ''
        tds = line.xpath("./td")
        if len(tds) < 2:
            continue
        if nb_columns == 0:
            nb_columns = len(tds)
        if len(tds) == nb_columns:
            date_info = [part for part in tds[1].itertext() if part]
            date_start = None
            date_end = None
            if date_info[0].startswith('Du '):
                try:
                    date_start = datetime.strptime(date_info[0], 'Du %d/%m/%Y').date()
                except ValueError:
                    date_start = datetime.strptime(f'{date_info[0]}/{datetime.now().year}', 'Du %d/%m/%Y').date()
                try:
                    date_end = datetime.strptime(date_info[-1], 'au %d/%m/%Y').date()
                except:
                    date_end = datetime.strptime(f'{date_info[-1]}/{datetime.now().year}', 'au %d/%m/%Y').date()
            elif date_info[0].startswith('Tous '):
                recurring_info = f'{date_info[0]}\n'
            elif date_info != ['A', 'C', 'T', 'U', 'E', 'L', 'L', 'E', 'M', 'E', 'N', 'T']:
                try:
                    date_start = datetime.strptime(date_info[-1], '%d %B %Y').date()
                except ValueError:
                    date_start = datetime.strptime(f'{date_info[-1]} {datetime.now().year}', '%d %B %Y').date()
            # handle rowspan so that column indexes are consistent
            tds = tds[1:]
        time_details = f'{recurring_info}{md(html.tostring(tds[1]))}'
        external_link = ''
        if '<http' in time_details:
            external_link = tds[1].text_content().strip()
            time_details = ''
        raw_description = html.tostring(tds[3])
        if len(tds) == 6:
            event = Event.create(
                category=category,
                date_start=date_start,
                date_end=date_end,
                time_details=time_details,
                place=md(html.tostring(tds[2])),
                description=md(raw_description),
                price=md(html.tostring(tds[4])),
                creation_date=None,
                created_by=md(html.tostring(tds[5])),
                external_link=external_link,
                highlight=True if b'class="highlight"' in raw_description else False
            )
        elif len(tds) == 5:
            event = Event.create(
                category=category,
                date_start=date_start,
                date_end=date_end,
                time_details=time_details,
                place=md(html.tostring(tds[2])),
                description=md(raw_description),
                creation_date=None,
                created_by=md(html.tostring(tds[4])),
                external_link=external_link,
                highlight=True if b'class="highlight"' in raw_description else False
            )
        else:
            raise Exception(
                f"Unexpected number of tds ({len(tds)})! {category}/{suffix}"
            )


def process_places(token):
    print("######### places")
    r = requests.get(f"https://agendainforme.htg0.com/admin/locations.php?sid={token}")
    page = r.text
    tree = html.fromstring(page)
    for line in tree.xpath("//tr"):
        tds = line.xpath("./td")
        if len(tds) < 2:
            continue
        place = Place.create(
            name=tds[0].text_content(), description=md(html.tostring(tds[1]))
        )


def main():
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    r = requests.get("https://agendainforme.htg0.com/admin/login.php")
    r = requests.post("https://agendainforme.htg0.com/admin/login.php",
                      data={'username': IMPORT_USERNAME, 'password': IMPORT_PASSWD},
                      cookies=r.cookies)
    parts = r.text.split('sid=')
    token = parts[1].split('"')[0]

    with db.atomic():
        process_places(token)
        for category in CATEGORIES:
            process(category, token)
            if IMPORT_ARCHIVES:
                process(category, token, '&archived=true')


if __name__ == "__main__":
    main()
