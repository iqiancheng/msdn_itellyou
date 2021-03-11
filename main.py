#!/usr/bin/env python
# coding:utf-8

"""
A 'Crawler' for http://msdn.itellyou.cn/
"""

import html
import json
import re
import sqlite3

import requests

dbconn = sqlite3.Connection('msdn.db')


def do_post(url, params):
    headers = {
        "x-csrf-token": "CfDJ8P98M0aeRU5JnqCGFmQBR508gX-gu9402AsX6G-MZ_Or1pLO1xzbOFVQa0pyxdS22uq7FunHI84xN0OxbGevr9j9ypkB7_yRUb28waMTo-bHALGoOhh-qTooBDkUkwijBNCQsu4SNsMiuupKuSa8TLo",
        "cookie": ".AspNetCore.Antiforgery.kC_Kc8he0KM=CfDJ8P98M0aeRU5JnqCGFmQBR52p6AN3WdRZ9voGEwZ_hg2mJCEJIE7pW142e2R45_vF2S2Vm-usfrnoDMLOC7WHqv7NKuvZm8-J-4hx3gBkujgxQryuUGaceNtlVjABCn6aglPm1GUxkub80jHZ0R6fXMY; never_show_donate_auto=true"
    }
    # Adding empty header as parameters are being sent in payload
    r = requests.post(url, data=params, headers=headers)
    return r.content


def get_menus():
    """
    (<id>,<name>)+
    """
    src = requests.get('https://msdn.itellyou.cn/')
    pattern = 'data-target=#collapse_(.*?)>(.*?)</a>'
    content = str(src.content, 'utf-8')
    return re.findall(pattern, content)


def get_sub_menus(mid):
    """
    ({'id':<id>,'name':<name>})+
    """
    src = do_post('https://msdn.itellyou.cn/Index/GetCategory', {'id': mid})
    return json.loads(src)


def get_lang_list(sid):
    """
    {"status":true,"result":({'id':<id>,'lang':<lang>})+}
    """
    src = do_post('https://msdn.itellyou.cn/Index/GetLang', {'id': sid})
    return json.loads(src)['result']


def get_iso_list(sid, lid):
    """
    {"status":true,"result":({'id':<id>,'name':<name>,'post':<date>,'url':<url>})+}
    """
    src = do_post('https://msdn.itellyou.cn/Index/GetList',
                  {'id': sid, 'lang': lid, 'filter': 'true'})
    return json.loads(src)['result']


def get_iso(iid):
    """
    {"status":true,"result":({'download':<url>,'filename':<fname>,
        'postdatestring':<2008-09-08>,'sha1':<sha1>,'size':<size>})+
    }
    """
    src = do_post('https://msdn.itellyou.cn/Index/GetProduct', {'id': iid})
    return json.loads(src)['result']


def unescape(str):
    # str = '&#x4F01;&#x4E1A;&#x89E3;&#x51B3;&#x65B9;&#x6848;'
    return html.unescape(str)


def create_db():
    c = dbconn.cursor()
    c.executescript("""
    DROP TABLE IF EXISTS iso;
    CREATE TABLE iso(
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name    TEXT,
        fname   TEXT,
        cate    TEXT,
        product TEXT,
        lang    TEXT,
        url     TEXT,
        sha1    TEXT,
        size    TEXT,
        date    datetime
    );
    """)
    dbconn.commit()
    c.close()


if __name__ == '__main__':
    create_db()
    c = dbconn.cursor()
    for menu in get_menus():
        for sub in get_sub_menus(menu[0]):
            for lang in get_lang_list(sub['id']):
                for iso in get_iso_list(sub['id'], lang['id']):
                    detail = get_iso(iso['id'])
                    print(detail['filename'])
                    c.execute('INSERT INTO iso(name, fname, cate, product, lang,'
                              'url, sha1, size, date)'
                              'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                              (iso['name'], detail['filename'],
                               unescape(menu[1]), sub['name'],
                               lang['lang'], detail[
                                   'download'], detail['sha1'],
                               detail['size'], detail['postdatestring'])
                              )
            dbconn.commit()
    c.close()
    dbconn.close()
    print("done.")
