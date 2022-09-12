import hashlib
import os
import requests
import json
import logging
import time
from utils.__init__ import img_extensions

html_cach_dir = '_html_cach/'

if not os.path.exists(html_cach_dir):
    os.mkdir(html_cach_dir)


def json_file_update(file, data):
    json.dump(data, open(file, 'w', encoding='utf-8'),
              sort_keys=True, indent=4, ensure_ascii=False)


def download_html_post(url, headers=None, data=None, files=None):
    r = None
    slp_time = 1
    for i in range(3):
        try:
            r = requests.post(url, headers=headers,
                              data=data, files=files)
            if r != None and r.status_code == 200:
                break
        except BaseException:
            logging.info(
                "download html failed, trying... %d url='%s'" % (i, url))
            time.sleep(slp_time)
            slp_time = slp_time*2

    if r != None and r.status_code == 200:
        r.encoding = r.apparent_encoding
        return r.text
    else:
        logging.info("download Failed, url='%s'" % (url))
    return None


def download_html_get(url: str, cach=True, headers=None, proxies=None):
    cach_file = html_cach_dir + os.sep + \
        hashlib.md5(url.encode(encoding='UTF-8')).hexdigest() + ".html"
    if os.path.exists(cach_file):
        ret = open(cach_file, "r").read()
        return ret

    r = None
    slp_time = 1
    for i in range(3):
        try:
            r = requests.get(url, headers=headers)
            if r != None and r.status_code == 200:
                break
        except BaseException:
            logging.info(
                "download html failed, trying... %d url='%s'" % (i, url))
            time.sleep(slp_time)
            slp_time = slp_time*2

    if r != None and r.status_code == 200:
        r.encoding = r.apparent_encoding
        with open(cach_file, "w+") as o:
            o.write(r.text)
        return r.text
    else:
        logging.info("download Failed, url='%s'" % (url))
    return None
