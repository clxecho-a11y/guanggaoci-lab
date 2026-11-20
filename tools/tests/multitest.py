import sys
from playwright.sync_api import sync_playwright
site, shots = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1320,'height':950}); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.goto('file://'+site+'/index.html'); pg.wait_for_timeout(600)
    print('mode hint:', pg.inner_text('#modeHint'))
    def refs():
        out=[]
        for li in pg.query_selector_all('#refList .ref'):
            out.append((li.get_attribute('data-set') and 'SET' or 'SEG', li.query_selector('.hd b').inner_text().replace('　',' '), li.query_selector('input').is_checked()))
        return out
    # 靖遠 紅海參 分 3 段
    pg.select_option('#fCh','jingyuan'); pg.select_option('#fCat','紅海參'); pg.check('input[name=mode][value="3"]', force=True); pg.wait_for_timeout(200)
    print('visible parts/slot/len:', pg.is_visible('#partsWrap'), pg.is_visible('#slotWrap'), pg.is_visible('#lenWrap'), '| badge', pg.inner_text('#badgeSec'), '|', pg.inner_text('#partsHint'))
    print('mode hint:', pg.inner_text('#modeHint')); print('refMeta:', pg.inner_text('#refMeta'))
    for r in refs(): print('   ', r)
    pg.fill('.prow[data-i="0"] .psec','25'); pg.select_option('.prow[data-i="2"] .ppos','後段'); pg.wait_for_timeout(150)
    pr=pg.input_value('#promptText'); open(shots+'/prompt-multi.txt','w',encoding='utf-8').write(pr)
    print('badge after edit', pg.inner_text('#badgeSec'), '| prompt len', len(pr))
    pg.click('#refList .ref:first-child [data-act=open]'); pg.wait_for_timeout(100)
    print('open set script parts:', len(pg.query_selector_all('#refList .ref:first-child .parthd')))
    pg.screenshot(path=shots+'/08-multi.png', full_page=True)
    draft='''【版本1｜省钱角度】
〈第1段｜片头｜约25秒〉
引入：节目开始之前先说一件事。
正文：蓝莓优品的黑五优惠已经开始了，用我的优惠码 TJY，红海参可以打85折，具体怎么领我们稍后再细说，大家先记住 TJY 这个优惠码，待会儿节目中间我会把满减和赠品一条一条讲清楚。
回正题：好，我们先进入今天的话题。
〈第2段｜中段｜约60秒〉
引入：讲到这里先休息一下，把刚才说的优惠讲清楚。
正文：''' + '这次黑五买红海参，输入优惠码 TJY 先打85折，折后满500美元再减30美元，还送建国250周年的纪念品，满900美元再加送一套珍藏的酒具。' + '我自己家里人一直在吃，早上一条很方便，不用泡发也不用炖，当然每个人的情况不同。想下单的朋友点视频下方描述栏的链接，或者扫屏幕上的二维码就可以了，记得结账时输入 TJY。' * 2 + '''
回正题：好，我们回到刚才的话题。
〈第3段｜后段｜约40秒〉
引入：节目最后再提醒大家一下。
正文：黑五的优惠到11月30号就截止了，想给家里长辈准备年终礼物的朋友可以抓紧时间，点描述栏的链接下单，红海参独立条装，送人自己吃都方便，时间不多了大家不要错过这一次全年力度最大的活动。
回正题：好，今天的节目就到这里，我们明天见。

【版本2｜重复测试】
〈第1段〉
引入：先说一件事。
正文：用优惠码 TJY 红海参打85折满500美元减30美元。
回正题：回来。
〈第2段〉
引入：再说一次。
正文：用优惠码 TJY 红海参打85折满500美元减30美元。
回正题：回来。

【提醒】版本1合适。'''
    pg.fill('#draft',draft); pg.click('#btnCheck'); pg.wait_for_timeout(200)
    print('status:', pg.inner_text('#checkStatus'))
    for f in pg.query_selector_all('.ver'):
        print('---', f.query_selector('header').inner_text().replace('\n',' | ')); print('   ', f.query_selector('.parts').inner_text().replace('\n',' '))
        for li in f.query_selector_all('.findings li'): print('    ', li.get_attribute('class'), li.inner_text().replace('\n',' '))
    pg.query_selector('#h4s').scroll_into_view_if_needed(); pg.screenshot(path=shots+'/09-multi-check.png')
    # 2 段、沒有分段紀錄的組合
    pg.select_option('#fCh','fangfei'); pg.select_option('#fCat','黑膏滋'); pg.check('input[name=mode][value="2"]', force=True); pg.wait_for_timeout(200)
    print('fangfei 2-part: notice=', (pg.inner_text('#refList .empty')[:60] if pg.query_selector('#refList .empty') else None), '|', pg.inner_text('#refMeta'), '| types', set(r[0] for r in refs()))
    pr2=pg.input_value('#promptText'); print('  fallback line in prompt:', '沒有分段講這個產品的紀錄' in pr2, '| 講法 line:', [l for l in pr2.split('\n') if l.startswith('- 講法')][0][:40])
    # 2 段 with sets
    pg.select_option('#fCh','weiyu'); pg.wait_for_timeout(200)
    print('weiyu 2-part:', pg.inner_text('#refMeta')); [print('   ',r) for r in refs()[:4]]
    # 回到一段
    pg.check('input[name=mode][value="1"]', force=True); pg.wait_for_timeout(200)
    print('single again: slot visible', pg.is_visible('#slotWrap'), '| types', set(r[0] for r in refs()), '|', pg.inner_text('#refMeta'), '| 廣告位 in prompt', '- 廣告位' in pg.input_value('#promptText'))
    # 口播庫
    pg.click('#viewLib'); pg.wait_for_timeout(200)
    pg.select_option('#lMode','m'); pg.wait_for_timeout(100); print('lib multi:', pg.inner_text('#libMeta'))
    pg.select_option('#lMode','1'); pg.wait_for_timeout(100); print('lib single:', pg.inner_text('#libMeta'))
    pg.select_option('#lMode','m'); pg.select_option('#lCh','fangwei'); pg.wait_for_timeout(150)
    pg.screenshot(path=shots+'/10-lib-multi.png')
    pg.click('#libList .card:first-child [data-act=use]'); pg.wait_for_timeout(250)
    print('after use: mode', pg.eval_on_selector('input[name=mode]:checked','e=>e.value'), 'ch', pg.input_value('#fCh'), 'cat', pg.input_value('#fCat'), '|', pg.inner_text('#refMeta'), '| write', pg.is_visible('#write'))
    m=b.new_page(viewport={'width':390,'height':800}); m.goto('file://'+site+'/index.html'); m.wait_for_timeout(500)
    m.check('input[name=mode][value="3"]', force=True); m.wait_for_timeout(200)
    print('mobile overflow', m.evaluate('document.documentElement.scrollWidth - window.innerWidth')); m.screenshot(path=shots+'/11-mobile-multi.png', full_page=True)
    b.close(); print('ERR', errs)
