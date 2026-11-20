import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1320,'height':950}); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.goto('file://'+sys.argv[1]+'/index.html'); pg.wait_for_timeout(600)
    print(pg.inner_text('#stamp'))
    def refs():
        return [ (li.query_selector('.hd b').inner_text().replace('　',' '), [x.inner_text() for x in li.query_selector_all('.tag.hi,.tag.lo,.tag.mid')], li.query_selector('input').is_checked()) for li in pg.query_selector_all('#refList .ref')]
    for ch,cat in [('tianliang','黑膏滋'),('fangwei','紅海參'),('jingyuan','紅海參'),('tianliang','會員網站')]:
        pg.select_option('#fCh',ch); pg.select_option('#fCat',cat); pg.wait_for_timeout(150)
        print('==',ch,cat,'| note:', pg.inner_text('#saleNote')[-60:] if pg.is_visible('#saleNote') else '(hidden)')
        for r in refs(): print('   ',r)
    pg.select_option('#fCh','tianliang'); pg.select_option('#fCat','黑膏滋'); pg.wait_for_timeout(150)
    pr=pg.input_value('#promptText')
    print([l[:70] for l in pr.split('\n') if l.startswith('〈參考') or l.startswith('有些參考')])
    pg.screenshot(path=sys.argv[2]+'/06-sale-refs.png', full_page=True)
    pg.click('#viewLib'); pg.wait_for_timeout(200)
    for v in ['hi','mid','lo','none','']:
        pg.select_option('#lSale',v); pg.wait_for_timeout(100); print('lib',v or 'all', pg.inner_text('#libMeta'))
    pg.select_option('#lSale','hi'); pg.select_option('#lCh','zaoan'); pg.wait_for_timeout(150)
    pg.screenshot(path=sys.argv[2]+'/07-sale-lib.png')
    m=b.new_page(viewport={'width':390,'height':800}); m.goto('file://'+sys.argv[1]+'/index.html'); m.wait_for_timeout(500)
    print('mobile overflow', m.evaluate('document.documentElement.scrollWidth - window.innerWidth'))
    b.close(); print('ERR',errs)
