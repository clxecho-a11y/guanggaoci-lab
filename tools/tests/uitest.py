import sys, json
from playwright.sync_api import sync_playwright
site, shots = sys.argv[1], sys.argv[2]
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1320,'height':950})
    pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
    pg.goto('file://'+site+'/index.html'); pg.wait_for_timeout(800)
    print('stamp:', pg.inner_text('#stamp'))
    print('refs default:', pg.inner_text('#refMeta'), '| offer:', repr(pg.input_value('#fOffer')[:120]), '| code:', pg.input_value('#fCode'))
    pg.screenshot(path=shots+'/01-default.png', full_page=True)
    # 方偉 紅海參 第二廣告位 100 秒
    pg.select_option('#fCh','fangwei'); pg.select_option('#fCat','紅海參')
    pg.check('input[name=slot][value="第二廣告位"]', force=True)
    pg.fill('#fSec','100'); pg.fill('#fTopic','五中全會後的人事變動')
    pg.check('#fFocus input[value="節日促銷"]', force=True)
    pg.wait_for_timeout(200)
    prompt=pg.input_value('#promptText')
    open(shots+'/prompt.txt','w',encoding='utf-8').write(prompt)
    print('prompt len',len(prompt), '| refMeta', pg.inner_text('#refMeta'), '| rate', pg.inner_text('#rateHint'), '| badge', pg.inner_text('#badgeSec'))
    print('bucket checked:', pg.eval_on_selector('input[name=bucket]:checked','e=>e.value'))
    pg.click('#refList .ref:first-child [data-act=open]'); pg.wait_for_timeout(100)
    draft='''**【版本1｜主持人自己的感受】**
引入：講到這裡先暫停一下，跟大家說個事。
正文：我自己每天錄節目很累，最近一直在吃紅海參，感覺精神好很多。現在黑五有85折，用優惠碼 fangwei 下單，折後滿399再減30，還送一瓶價值38美元的滴劑。它能治療關節炎，保證有效，還買二送一，只要199。點描述欄的連結就可以下單。
回正題：好，我們接著講五中全會。

## 版本2：限時優惠
引入：〔接今天話題〕
正文：黑五優惠只到月底。
回正題：回到正題。

【提醒】版本1最適合。'''
    pg.fill('#draft',draft); pg.click('#btnCheck'); pg.wait_for_timeout(200)
    print('check status:', pg.inner_text('#checkStatus'))
    for f in pg.query_selector_all('.ver'):
        print('---', f.query_selector('header').inner_text().replace('\n',' | '))
        print('   parts:', f.query_selector('.parts').inner_text().replace('\n',' '))
        for li in f.query_selector_all('.findings li'): print('   ', li.get_attribute('class'), li.inner_text().replace('\n',' '))
    print('rank:', pg.inner_text('.rank'))
    print('marks:', [m.inner_text() for m in pg.query_selector_all('.ver mark')])
    pg.screenshot(path=shots+'/02-fangwei-check.png', full_page=True)
    # 沒有紀錄的組合
    pg.select_option('#fCh','zhenguandian'); pg.select_option('#fCat','蔘皇'); pg.wait_for_timeout(150)
    print('no-history:', pg.inner_text('#refList .empty') if pg.query_selector('#refList .empty') else 'none', '|', pg.inner_text('#refMeta'))
    pg.select_option('#fCat','其他產品'); pg.wait_for_timeout(100)
    print('other visible:', pg.is_visible('#fOther'))
    # 會員網站：不帶優惠碼、不帶保健規則
    pg.select_option('#fCh','tianliang'); pg.select_option('#fCat','會員網站'); pg.wait_for_timeout(150)
    pr=pg.input_value('#promptText')
    print('member: code=',repr(pg.input_value('#fCode')),'| 保健 rule' , '保健食品的廣告' in pr, '| 天亮 rule', '其他主持人' in pr)
    # 口播庫
    pg.click('#viewLib'); pg.wait_for_timeout(200)
    print('lib meta:', pg.inner_text('#libMeta'), 'cards', len(pg.query_selector_all('#libList .card')))
    pg.select_option('#lCh','weiyu'); pg.fill('#lQ','滴劑'); pg.wait_for_timeout(200)
    print('lib filtered:', pg.inner_text('#libMeta'))
    pg.screenshot(path=shots+'/03-lib.png', full_page=False)
    pg.click('#libList .card:first-child [data-act=use]'); pg.wait_for_timeout(200)
    print('after use: ch', pg.input_value('#fCh'), 'cat', pg.input_value('#fCat'), 'refs', pg.inner_text('#refMeta'), 'write visible', pg.is_visible('#write'))
    # copy
    ctx=b.new_context(permissions=['clipboard-read','clipboard-write'], viewport={'width':390,'height':800})
    m=ctx.new_page(); m.on('pageerror', lambda e: errs.append('M PAGEERR '+str(e)))
    m.goto('file://'+site+'/index.html'); m.wait_for_timeout(600)
    m.click('#btnCopy'); m.wait_for_timeout(300)
    print('copy status:', m.inner_text('#copyStatus'))
    print('mobile overflow px:', m.evaluate('document.documentElement.scrollWidth - window.innerWidth'))
    m.screenshot(path=shots+'/04-mobile.png', full_page=True)
    b.close()
print('ERRORS:', errs)
