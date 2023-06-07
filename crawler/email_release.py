import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from crawler.config import *


def receivers():
    s = ''
    for item in MAIL_RECEIVERS:
        s += f'{item}<{item}>'
    return s


def send_email(subject_content, body_content, attachment=None):
    mm = MIMEMultipart('related')
    # 邮件主题
    # 设置发送者,注意严格遵守格式,里面邮箱为发件人邮箱
    mm["From"] = f"{MAIL_SENDER}<{MAIL_SENDER}>"
    # 设置接受者,注意严格遵守格式,里面邮箱为接受者邮箱
    mm["To"] = receivers()
    # 设置邮件主题
    mm["Subject"] = Header(subject_content, 'utf-8')
    # 邮件正文内容
    # body_content = """你好，这是一个测试邮件！"""
    # 构造文本,参数1：正文内容，参数2：文本格式，参数3：编码方式
    message_text = MIMEText(body_content, "plain", "utf-8")
    # 向MIMEMultipart对象中添加文本对象
    mm.attach(message_text)
    stp = smtplib.SMTP()
    # 设置发件人邮箱的域名和端口，端口地址为25
    stp.connect(MAIL_HOST, MAIL_HOST_PORT)
    # set_debuglevel(1)可以打印出和SMTP服务器交互的所有信息
    stp.set_debuglevel(1)
    # 登录邮箱，传递参数1：邮箱地址，参数2：邮箱授权码
    stp.login(MAIL_SENDER, password=MAIL_PASSWORD)
    if attachment:
        atta = MIMEText(open(attachment, 'rb').read(), 'base64', 'utf-8')
        atta["Content-Type"] = 'application/octet-stream'
        # 设置附件信息
        atta.add_header("Content-Disposition", "attachment",
                        filename=("gbk", "", attachment))  # 添加附件到邮件信息当中去
        mm.attach(atta)
    # 发送邮件，传递参数1：发件人邮箱地址，参数2：收件人邮箱地址，参数3：把邮件内容格式改为str
    stp.sendmail(MAIL_SENDER, MAIL_RECEIVERS, mm.as_string())
    print("邮件发送成功")
    # 关闭SMTP对象
    stp.quit()


if __name__ == '__main__':
    send_email('采购意向汇总爬虫', 'bbb', attachment='广东省国土资源技术中心-采购意向公告.md')