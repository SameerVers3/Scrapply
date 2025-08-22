from app.core.agent import UniversalHtmlAnalyzer
html='''<html><body><div class="items"><div class="item"><h2>Title</h2><p>$10</p></div><div class="item"><h2>Other</h2><p>$20</p></div></div></body></html>'''
a=UniversalHtmlAnalyzer(html)
best,score=a.analyze()
print('score=',score)
if best is not None:
    print('best tag:', best.name)
    print('semantics:', a._analyze_container_semantics(best))
    print('samples:', a._extract_intelligent_samples(best, a._analyze_container_semantics(best)['item_container_selector']))
else:
    print('no best container found')
