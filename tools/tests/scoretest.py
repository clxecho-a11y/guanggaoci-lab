import sys
from playwright.sync_api import sync_playwright
good = '''【版本1｜主持人自己的感受】
引入：讲到这里，我先跟大家说个事，说完我们马上回来。
正文：''' + '我自己每天录节目，坐在电脑前面的时间很长，最近这段时间一直在吃黑膏滋，早上一小勺，感觉精神比以前好一些，当然每个人情况不同。' * 2 + '''现在正好是黑五，用我的优惠码 TLTime 下单可以打85折，折后满399美元再减30美元，预售期间还送一瓶价值38美元的西洋参黑膏滋滴剂，送完为止。想试试的朋友，点视频下方的购买链接，或者扫描屏幕上的二维码，不方便网购可以打 18003688878 由客服帮你下单。记得结账的时候输入优惠码 TLTime。
回正题：好，我们回到今天的话题。

【提醒】版本1合适。'''
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1320,'height':950}); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://'+sys.argv[1]+'/index.html'); pg.wait_for_timeout(600)
    pg.fill('#draft', good); pg.click('#btnCheck'); pg.wait_for_timeout(200)
    for f in pg.query_selector_all('.ver'):
        print(f.query_selector('header').inner_text().replace('\n',' | ')); print(f.query_selector('.parts').inner_text().replace('\n',' '))
        for li in f.query_selector_all('.findings li'): print('  ', li.get_attribute('class'), li.inner_text().replace('\n',' '))
    pg.query_selector('#h4s').scroll_into_view_if_needed()
    pg.screenshot(path=sys.argv[2]+'/05-score.png', full_page=True)
    b.close(); print('ERR', errs)
