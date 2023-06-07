from crawler.config import *
from md2cf.api import MinimalConfluence
import mistune
from md2cf.confluence_renderer import ConfluenceRenderer


def md2cf(file_path, title):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    renderer = ConfluenceRenderer(use_xhtml=True)
    confluence_mistune = mistune.Markdown(renderer=renderer)
    confluence_body = confluence_mistune(content)
    confluence = MinimalConfluence(host=CONF_API, username=CONF_USERNAME, password=CONF_PASSWORD)
    page = confluence.get_page(title=title, space_key=CONF_TARGET_SPACE)
    confluence.update_page(page=page, body=confluence_body, update_message='每日更新')
    print(f'--------------------{title}自动更新已完成--------------------')