from crawler import auto_mark
from crawler.email_release import send_email
from crawler.config import *
import time
import tabulate
import schedule


def run():
    startTime = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())
    print(startTime, '开始爬取')
    auto_mark()
    endTime = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())
    print(endTime, '爬取结束')
    today = time.strftime('%Y年%m月%d日', time.localtime())
    classes = ','.join(TARGETS)
    email_sub = f'{today}采购意向汇总已更新'
    email_content = f'包含{classes}的采购意向公告汇总已更新完成，请前往http://139.159.148.93:8090/pages/viewpage.action?pageId=12451984' \
                    f'查看。\n爬虫开始时间：{startTime}\n爬虫结束时间：{endTime} '
    send_email(email_sub, email_content)


if __name__ == '__main__':
    schedule.every().day.at("07:30:00").do(run)
    while True:
        schedule.run_pending()
