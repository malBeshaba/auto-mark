import os
from typing import Union, Any
import requests
import time
import pytesseract
import json
import pandas as pd
from tqdm import tqdm
from crawler.md2cf_mode import md2cf
import numpy as np
from crawler.config import TARGETS

np.set_printoptions(suppress=True)
pd.set_option('display.float_format', lambda x: '%.0f' % x)


def getVertifyImage():
    url = 'https://gdgpo.czt.gd.gov.cn/freecms/verify/verifyCode.do?createTypeFlag=n&name=notice&d' + str(
        round(time.time() * 1000))
    try:
        response = requests.get(url)
        with open(os.path.join(os.path.abspath("."), 'vertify.jpg'), 'wb') as f:
            f.write(response.content)
    except requests.exceptions.ConnectionError:
        time.sleep(0.5)
        getVertifyImage()


def analysisVertifyCode(img_path):
    # --psm 7 单行识别 , --oem 3 使用 LSTM OCR 引擎 , -c tessedit_char_whitelist=0123456789 只识别数字字符，也可以设置英文字母哦。
    num = pytesseract.image_to_string(img_path, lang='eng', config='--psm 7 --oem 3 -c '
                                                                   'tessedit_char_whitelist=0123456789')
    return num


def getMarkByKeywards(verify, purchaser, title, page, noticeType):
    # print('jj', verify)
    url = f'https://gdgpo.czt.gd.gov.cn/freecms/rest/v1/notice/selectInfoMoreChannel.do?&siteId=cd64e06a-21a7-4620' \
          f'-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d&currPage={page}&pageSize=10&noticeType' \
          f'={noticeType}&regionCode=440001&verifyCode={verify}&subChannel=false&purchaseManner=&title={title}&openTenderCode=&purchaser' \
          f'={purchaser}&agency=&purchaseNature=&operationStartTime=&operationEndTime=&selectTimeName=noticeTime' \
          f'&cityOrArea= '
    try:
        response = requests.get(url)
        return json.loads(response.text)
    except requests.exceptions.ConnectionError:
        time.sleep(0.5)
        return getMarkByKeywards(verify, purchaser, title, page, noticeType)


def requestLoop(purchaser='', title='', page=1, noticeType='') -> dict:
    while 1:
        vertifyCode = analysisVertifyCode(os.path.join(os.path.abspath("."), 'vertify.jpg'))
        s = "".join([i for i in vertifyCode if i.isalpha() or i.isnumeric()])
        res = getMarkByKeywards(s, purchaser, title, page=page, noticeType=noticeType)
        if res['msg'] == '操作成功':
            return res
        else:
            time.sleep(0.5)
            getVertifyImage()


def getType(noticeType) -> str:
    types_match = {'001051': '单一来源公示', '001101': '采购计划', '001059': '采购需求', '001052': '资格预审',
                   '001053': '资格预审', '00101': '采购公告', '00102': '中标公告', '00103': '更正公告',
                   '001004': '终止公告', '001006': '终止公告', '001054': '合同公告', '001009': '验收公告',
                   '00105A': '验收公告', '59': '采购意向公告'}
    for key, value in types_match.items():
        if key in noticeType:
            return value
    return '其他'


def auto_mark_all(keyward):
    oceanCenter = requestLoop(keyward)
    ocList = []
    for data in oceanCenter['data']:
        ocList.append([data['title'], data['noticeTime'], data['regionName'], getType(data['noticeType']),
                       data['catalogueNameList'],
                       data['purchaser'], f'[点击查看公告](https://gdgpo.czt.gd.gov.cn{data["pageurl"]})'])
    for i in range(0, int(oceanCenter['total'] / 10)):
        oceanCenter = requestLoop(keyward, page=i + 2)
        for data in oceanCenter['data']:
            ocList.append([data['title'], data['noticeTime'], data['regionName'], getType(data['noticeType']),
                           data['catalogueNameList'],
                           data['purchaser'], f'[点击查看公告](https://gdgpo.czt.gd.gov.cn{data["pageurl"]})'])
    ocDF = pd.DataFrame(ocList, columns=['标题', '发布时间', '公告级别', '公告类型', '采购品目', '采购人', '公告链接'])
    print(ocDF)
    ocDF.to_markdown(os.path.join(os.path.abspath("."), keyward + '-采购公告.md'), index=False)
    os.system(f'md2cf --host http://139.159.148.93:8090/rest/api --username wangshenyu --password @Wsyxxbb111 --space '
              f'~wangshenyu {keyward}-采购公告.md')


def auto_mark_intention(keyward):
    oceanCenter = requestLoop(keyward, noticeType='59')
    ocList = []
    for data in oceanCenter['data']:
        html = f'https://gdgpo.czt.gd.gov.cn{data["pageurl"]}'
        parentTitle = data['title']
        noticeTime = data['noticeTime']
        for item in list(getTableFromHtml(html)):
            ocList.append([parentTitle, noticeTime] + item)
    for i in range(0, int(oceanCenter['total'] / 10)):
        oceanCenter = requestLoop(keyward, page=i + 2, noticeType='59')
        for data in oceanCenter['data']:
            html = f'https://gdgpo.czt.gd.gov.cn{data["pageurl"]}'
            parentTitle = data['title']
            noticeTime = data['noticeTime']
            for item in list(getTableFromHtml(html)):
                ocList.append([parentTitle, noticeTime] + item)
    ocDF = pd.DataFrame(ocList, columns=['标题', '发布时间', '采购项目名称', '采购需求概况', '落实政府采购政策情况',
                                         '预算金额(元)', '预计采购时间', '备注'])
    ocDF = removeOldTender(ocDF)
    ocDF['预算金额(元)'] = ocDF['预算金额(元)'].astype(np.int64).astype(str)
    ocDF = mergeTenderDetailAndResult(ocDF)
    savePath = os.path.join(os.path.abspath("."), keyward + '-采购意向公告.md')
    ocDF.to_markdown(savePath, index=False)
    md2cf(savePath, keyward + '-采购意向公告')


def getTableFromHtml(html) -> Union[object, list[Any]]:
    df = pd.read_html(html, encoding='utf-8')[0]
    try:
        return df.drop(columns='序号').values.tolist()
    except:
        print(df)
        return []


def auto_mark_intention2(keyward):
    oceanCenter = requestLoop(keyward, noticeType='59')
    ocList = []
    for data in oceanCenter['data']:
        html = f'https://gdgpo.czt.gd.gov.cn{data["pageurl"]}'
        parentTitle = data['title']
        noticeTime = data['noticeTime']
        for item in list(getTableFromHtml(html)):
            ocList.append([parentTitle, noticeTime] + item)
    for i in range(0, int(oceanCenter['total'] / 10)):
        oceanCenter = requestLoop(keyward, page=i + 2, noticeType='59')
        for data in oceanCenter['data']:
            html = f'https://gdgpo.czt.gd.gov.cn{data["pageurl"]}'
            parentTitle = data['title']
            noticeTime = data['noticeTime']
            for item in list(getTableFromHtml(html)):
                ocList.append([parentTitle, noticeTime] + [str(i) for i in item])
    ocDF = pd.DataFrame(ocList, columns=['标题', '发布时间', '采购项目名称', '采购需求概况', '落实政府采购政策情况',
                                         '预算金额(元)', '预计采购时间', '备注'])
    ocDF.to_excel(keyward + '-采购意向公告.xlsx', index=False)


def titleRstrip(title):
    return title.rstrip('技术研究').rstrip('研究')


def getTenderDetailByTitle(title):
    res = requestLoop(title=title, noticeType='00101')
    if res['total'] == 0:
        return ['暂无', '暂无']
    else:
        data = res['data'][0]
        return [f'[点击查看招标公告](https://gdgpo.czt.gd.gov.cn{data["pageurl"]})', data['openTenderTime']]


def getTenderResultByTitle(title):
    res = requestLoop(title=title, noticeType='00102')
    if res['total'] == 0:
        return '暂无'
    else:
        data = res['data'][0]
        return f'[点击查看中标公告](https://gdgpo.czt.gd.gov.cn{data["pageurl"]})'


def deal_str(data):
    data = str(data) + '\t'
    return data


def removeOldTender(odf):
    L = []
    i = 0
    for date in tqdm(odf['预计采购时间']):
        if '2023' not in str(date):
            L.append(i)
        i += 1
    odf = odf.drop(index=L)
    return odf


def mergeTenderDetailAndResult(odf):
    t1List = []
    t2List = []
    t3List = []
    for title in tqdm(odf['采购项目名称']):
        tr = titleRstrip(title)
        td = getTenderDetailByTitle(tr)
        trr = getTenderResultByTitle(titleRstrip(title))
        t1List.append(td[0])
        t2List.append(td[1])
        t3List.append(trr)
    odf.insert(loc=len(odf.columns), column='招标公告', value=t1List)
    odf.insert(loc=len(odf.columns), column='开标时间', value=t2List)
    odf.insert(loc=len(odf.columns), column='中标公告', value=t3List)
    return odf


def auto_mark():
    for target in TARGETS:
        print(f'--------------------{target}自动采集开始--------------------')
        auto_mark_intention(target)
        print(f'--------------------{target}自动采集已完成--------------------')
