from difflib import IS_LINE_JUNK
import os
import json
import requests
import re
from lxml import etree
from zmq import proxy
from utils.utils import download_html_get, json_file_update

info_json_file = "stu_info.json"

headers = {
    "cookie": "JSESSIONID=1561722A4CBE930123037753D33FA688.student52_1; clwz_blc_pst_StudentCP=886384330.44575",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}


def get_id_list(yearid: int) -> list:
    url = "http://xsgl.7i5q.cas.scut.edu.cn/sms2/student/evaluation/evaluationList.jsp?classYearId=" + \
        str(yearid)
    web_text = download_html_get(url=url, headers=headers, proxies={
                                 "http": None, "https": None})
    web_info = etree.HTML(web_text).xpath(
        '//*[@id="pageForm"]/table/tr[3]/td/table[2]/tr')

    stu_info = {}
    if os.path.exists(info_json_file):
        stu_info = json.load(open(info_json_file, "r", encoding='utf-8'))
    for stu in web_info:
        href = stu.xpath("td[6]/a/@href")
        if len(href) > 0:
            href = href[0]
            info_text = stu.xpath("td[2]/a/@onmouseover")[0]
            name = re.findall(r"姓名：(\S+)<br>", info_text)[0]
            stu_id = re.findall(r"学号：(\S+)<br>", info_text)[0]
            score_url = "http://xsgl.7i5q.cas.scut.edu.cn"+href
            if name in stu_info:
                if score_url not in stu_info[name]["score_url"]:
                    stu_info[name]["score_url"].append(score_url)
            else:
                info = {
                    "id": stu_id,
                    "origin_info": info_text,
                    "score_url": [score_url]
                }
                stu_info.update({name: info})

    json_file_update(file=info_json_file, data=stu_info)


def get_score(url):
    html_text = download_html_get(url=url, headers=headers, proxies={
        "http": None, "https": None})
    yearid = re.findall(r"classYearId=([0-9]+)", url)[0]

    usr_info = etree.HTML(html_text).xpath(
        '//*[@id="pageForm"]/table/tr[2]/td/table/tr[1]/td')[0].text
    name, stu_id = re.findall(r"：(\S+)\s", usr_info)

    def get_from_form(sub_list):
        ret = []
        for sub in sub_list:
            sub_info = sub.xpath("td")
            if len(sub_info) > 5:
                sub_name = sub_info[0].text
                sub_score_text = sub_info[1].text
                sub_credit = float(sub_info[2].text)
                sub_type = sub_info[3].text
                sub_score = re.findall(r"([0-9.]+)", sub_score_text)[0]
                sub_score = float(sub_score)
                curr = {
                    "name": sub_name,
                    "score": sub_score,
                    "credict": sub_credit,
                    "type": sub_type,
                }
                ret.append(curr)
        return ret
    sub_list_1 = etree.HTML(html_text).xpath(
        '//*[@id="pageForm"]/table/tr[4]/td/table[2]/tr')
    sub_name_1 = etree.HTML(html_text).xpath(
        '//*[@id="pageForm"]/table/tr[4]/td/table[1]/tr/td')[0].text + f" yearid({yearid})"

    sub_list_2 = etree.HTML(html_text).xpath(
        '//*[@id="pageForm"]/table/tr[4]/td/table[5]/tr')
    sub_name_2 = etree.HTML(html_text).xpath(
        '//*[@id="pageForm"]/table/tr[4]/td/table[4]/tr/td')[0].text + f" yearid({yearid})"
    ret = {
        sub_name_1: get_from_form(sub_list_1),
        sub_name_2: get_from_form(sub_list_2),
    }
    return ret


def get_all_score():
    stu_info = json.load(open(info_json_file, "r", encoding='utf-8'))

    name_list = [name for name in stu_info]
    for name in name_list:
        ret = {}
        for url in stu_info[name]["score_url"]:
            try:
                ret.update(get_score(url))
            except IndexError:
                pass
        credict_sum = 0
        score_sum = 0
        for team in ret:
            for sub in ret[team]:
                if "专业" in sub["type"]:
                    credict_sum = credict_sum + sub["credict"]
                    score_sum = score_sum + sub["score"]*sub["credict"]
        stu_info[name].update(
            {"score": {"avg_score": score_sum/max(1, credict_sum), "details": ret}})

    json_file_update(file=info_json_file, data=stu_info)

def get_rank():
    stu_info = json.load(open(info_json_file, "r", encoding='utf-8'))

    name_list = [(stu_info[name]["score"]["avg_score"], name) for name in stu_info]
    name_list.sort()
    name_list.reverse()
    for i in range(len(name_list)):
        print(i+1, name_list[i][1], name_list[i][0])

def get_rank_year(yearid):
    stu_info = json.load(open(info_json_file, "r", encoding='utf-8'))

    name_list = []

    for name in stu_info:
        ret = stu_info[name]["score"]["details"]
        credict_sum = 0
        score_sum = 0
        for team in ret:
            if str(yearid) in team:
                for sub in ret[team]:
                    if "专业" in sub["type"]:
                        credict_sum = credict_sum + sub["credict"]
                        score_sum = score_sum + sub["score"]*sub["credict"]
        name_list.append( (score_sum/max(1, credict_sum),name) )

    name_list.sort()
    name_list.reverse()
    for i in range(len(name_list)):
        print(i+1, name_list[i][1], name_list[i][0])


def main():
    # get_id_list(yearid=15)
    # get_id_list(yearid=16)
    # get_all_score()
    get_rank()

    # get_rank_year(16)


if __name__ == "__main__":
    # main(sys.argv)
    main()
