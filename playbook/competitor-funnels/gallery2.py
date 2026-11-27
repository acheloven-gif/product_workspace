import base64,glob,io,re
SP='/tmp/claude-0/-home-user-product-workspace/af331c91-c80e-536b-a498-6257d22422c7/scratchpad/'
from PIL import Image
D='references/robella-competitors/'
def b64(path,w=390):
    im=Image.open(path).convert('RGB'); im=im.resize((w,int(im.size[1]*w/im.size[0])))
    bio=io.BytesIO(); im.save(bio,'JPEG',quality=72); return base64.b64encode(bio.getvalue()).decode()
def files(k): return sorted(f for f in glob.glob(D+k+'-*.jpg') if re.fullmatch(re.escape(D+k)+r'-\d+\.jpg',f))
A=lambda u,t: f'<a href="{u}" target="_blank" rel="noopener">{t}</a>'
nat='/tmp/claude-0/-home-user-product-workspace/af331c91-c80e-536b-a498-6257d22422c7/images/2.png'
robsec=f'<section id="robella"><h2>Наша воронка — Robella</h2><p class="sub">{A("https://f.robella.app/ai-stylist","f.robella.app/ai-stylist")} · экран возраста в окне 390×650 — снимок Наташи 26.11. Нижний ряд «40–49» и «50+» не помещается.</p><div class="strip"><figure><img loading="lazy" src="data:image/jpeg;base64,{b64(nat)}"><figcaption>Экран возраста</figcaption></figure></div></section>'
ADC=[('en','EN · Style Better Daily · с 16.11'),('pt','PT · Inspoy Hair Studio · с 27.10, 2 копии'),('ja','JA · видео · Stylist: Outfit Maker · с 13.11'),('ar','AR · видео · Stylist: Palette Finder · с 24.11')]
ADS='<h3>Реклама, которая ведёт на эту воронку</h3><p class="sub">Meta Ad Library, активные объявления на 27.11.2026. Все ведут на sub.stylix.app/quiz-pp?mode=hairstyle.</p><div class="strip">'+''.join(f'<figure style="flex:0 0 280px"><img loading="lazy" style="width:280px" src="data:image/jpeg;base64,{b64(D+"inspoy-ad-"+k+".jpg",432)}" alt="Реклама Inspoy {c}"><figcaption>{c}</figcaption></figure>' for k,c in ADC)+'</div>'

def figs(k,idx=None,title=''):
    fs=files(k); idx=idx or list(range(1,len(fs)+1))
    return ''.join(f'<figure><img loading="lazy" src="data:image/jpeg;base64,{b64(fs[i-1])}" alt="{title}, экран {i}"><figcaption>{i}</figcaption></figure>' for i in idx)
def strip(x): return f'<div class="strip">{x}</div>' if x else ''
def link(u): return A(u,u.replace("https://","").replace("&amp;","&"))
# app: (id, name, verdict, tyver_line, diff, main_funnel(key,url,desc,idx), extra_html, kids[(key,title,url,desc,idx)])
APPS=[
('dressly','Dressly','лидер по объёму: больше всех объявлений и показов',
 '56 617 объявлений за 30 дней, 7,6 млн показов в ЕС, самое долгое объявление — 9 дней. Реклама от страниц «экспертов по онлайн-шопингу» (Lilith Parker, Jenny Mitchell, Sienna Walker), 9 языков, вся Европа. Креативы меняют быстро.',
 'Загрузки нет: первый экран сразу рейтинг, обещание и возраст плитками с фото. Заход «понравиться мужчине» («Make him obsessed»): вопросы про отношения, свидания, комплименты. План гардероба с вещами из Shein. Оплата — план со скидкой через скретч-карту и таймер 10 минут: 4 недели $11.29, потом $49.99; 12 недель $29.99, потом $99.99; 24 недели $49.99, потом $119.99. У нас триал $1, потом $39.90 в месяц.',
 ('dressy','https://quiz.dressy.page/r?land=en%2Ffb-shop-shein-plan-rl-tech','новый домен Dressly, на него идёт вся реклама. Пройдено до пейвола',None),'',
 [('dressly','Dressly — старый домен','https://quiz.dressly.world/en/new-general-smart-plan-hp-4w-2','та же компания, заход «покупки онлайн без возвратов»: первый блок вопросов (экраны 2–8) — доверяете ли покупкам онлайн, бывают ли «сюрпризы» в заказе, приходилось ли возвращать вещи. В Tyver рекламы на этот домен за 30 дней нет','all'),
  ('dressly-fb','Dressly — старый домен, fb','https://quiz.dressly.world/en/fb-female-general-general','точь-в-точь как предыдущая: те же 36 экранов. Разница только в одном слове заголовка скретч-карты («Amazon» вместо «Personalized»)',None)]),
('inspoy','Inspoy','масштабируют: много показов, растут',
 '4 094 объявления за 30 дней, 6,2 млн показов в ЕС, самое долгое — 22 дня. Главная воронка — «причёски» (4,4 млн показов), дальше «цветотип» (1,1 млн) и «уход за кожей» (0,3 млн).',
 'Первый экран — лендинг с кнопкой Start, возраст на 3-м экране текстовыми кнопками в столбик.',
 ('inspoy','https://sub.stylix.app/quiz-pp?mode=hairstyle&amp;creative_topic=hairstyle','режим «причёски». Реклама обещает примерку причёсок по фото (креативы ниже), но в воронке о причёсках ничего нет: 17 вопросов про одежду, цвет и фигуру, потом фото лица для анализа цвета и почта. Пройдено до почты',None),'ADS',
 [('inspoy-colortype','Inspoy — цветотип','https://sub.stylix.app/quiz-pp?mode=colortype','95 объявлений, 1,1 млн показов. Не проходили',None),
  ('inspoy-skincare','Inspoy — уход за кожей','https://sub.stylix.app/quiz-pp?mode=skincare','96 объявлений, 0,3 млн показов. Не проходили',None),
  ('inspoy-other','Inspoy — гардероб, лукбук, маникюр','https://sub.stylix.app/quiz-pp?mode=wardrobe','по 4–14 объявлений, до 50 тыс. показов. Не проходили',None)]),
('mosso','Mosso','стабильно: самые долгие объявления',
 '3 868 объявлений за 30 дней, 2,0 млн показов в ЕС, самое долгое — 30 дней (весь период). Главная воронка — основная v3-4w (1,25 млн показов).',
 'Оплата — план на 4/8/16 недель со скидкой и таймером, у нас триал $1, потом $39.90 в месяц.',
 ('mosso','https://mosso.ai/mid/v3-4w/quiz','основная, до пейвола. Tyver: 398 объявлений, 1,25 млн показов',None),'',
 [('mosso-amz','Mosso — Amazon','https://mosso.ai/mid/8wupfreeblgl-amz/quiz','Tyver: 38 объявлений, 0,46 млн показов. Своих экранов только 2 первых, они ниже: заход «гардероб с Amazon» и экран «Your 30s wardrobe edit» вместо вопроса про возраст. Дальше те же вопросы, что в основной, отличаются только формулировки',[1,2]),
  ('mosso-pt','Mosso — португальская','https://mosso.ai/pt/mid/8wupfreebupd2v1-v4sub1skipleg/quiz','Tyver: 36 объявлений, 0,13 млн показов. Та же основная воронка на португальском — тестируют другое гео',None),
  ('mosso-pp','Mosso — pp','https://mosso.ai/mid/8wupfreebupd2v1-pp/quiz','Tyver: 20 объявлений, 0,12 млн показов. Точь-в-точь как основная, разница только в плашке «Black Friday code applied» на пейволе',None),
  ('mosso-es','Mosso — испанская','https://mosso.ai/es/mid/armario-capsula/quiz','Tyver: 6 объявлений, 26 тыс. показов. Та же основная воронка на испанском — тестируют другое гео',None)]),
('hairio','Hairio','растёт: новый, много показов на объявление',
 '669 объявлений за 30 дней, 1,8 млн показов в ЕС, самое долгое — 14 дней. Страницы «Hairio Pro», «Hairio App».',
 'Это подбор мужской стрижки (фейд, андеркат, «что сказать барберу»), а не стиль одежды. Возраст и пол не спрашивают, в конце обязательное селфи.',
 ('hairio','https://quiz.hairio.app/','новый конкурент, найден в Tyver 27.11. Пройдено до селфи',None),'',[]),
('stylio','Stylio','тестируют: много объявлений, мало показов',
 '3 421 объявление за 30 дней, 0,3 млн показов в ЕС, самое долгое — 27 дней. Реклама с 7.10.',
 'Загрузки нет: первый экран сразу рейтинг, обещание «капсульный гардероб» и возраст. Дальше два блока: внешность (8 вопросов) и предпочтения (23), среди них карточки образов «Would you wear it?» и выбор любимых магазинов логотипами.',
 ('stylio','https://quiz.stylio.fashion/?cohort=stylio_capsule_io0','пройдено до почты, после неё автопроход упёрся в ошибку',None),'',[]),
('vera','Vera (Great Apps)','тестируют: мало показов',
 '383 объявления за 30 дней, 64 тыс. показов в ЕС, самое долгое — 10 дней. Страницы «Your Personal AI Stylist» и «Jack — Stylist for Men».',
 'Перед возрастом — лендинг и экран-обещание. Возраст — 4 диапазона текстовыми кнопками.',
 ('vera','https://vera.greatapps.co/ver-gen-01-04/index.html','новый конкурент, найден в Tyver 27.11. Пройдено 15 экранов, дальше автопроход застрял на оценке по шкале 1–5',None),'',[]),
('refix','Refix AI','только запустили',
 '25 объявлений, реклама с 21.11, показов почти нет.',
 'Это подбор стрижки по форме лица. Возраст не спрашивают, на 2-м экране — пол. На 7-м экране нужно загрузить минимум 3 фото лица.',
 ('refix','https://quiz.refixai.app/zc/1641','новый конкурент. Пройдено до загрузки фото',None),'',[]),
('myswatches','Myswatches','мало, только США',
 '75 объявлений за 30 дней, только США — показов Tyver не видит.',
 'Возраст не спрашивают: лендинг с двумя кнопками, потом 8 вопросов про цвет. Без подписки: разовая покупка физической карты цветов за $29.99–39.99.',
 ('myswatches','https://myswatchesquiz.netlify.app/','квиз; до шага с фото. Ещё реклама ведёт сразу на товар без квиза: myswatches.com/products/swatchs, gift.myswatches.com',None),'',[]),
('kstyler','K-Styler','нет данных',
 'В Tyver рекламы нет — похоже, крутятся только на США. В Meta Ad Library на 26.11 было 11 активных объявлений, самое старое — 120 дней.',
 'Загрузки нет: первый экран сразу рейтинг, обещание и возраст плитками с фото. Оплата — 4 недели за $14.99, потом $49.99, а не триал $1.',
 ('kstyler','https://quiz.mykstyler.com/quizv1-sgo','основная; автопроход до бюджета',None),'',
 [('kstyler-mvp','K-Styler — MVP','https://quiz.mykstyler.com/quizv1-mvp-final','полная копия основной: прошли обе до почты, все 30 экранов совпадают слово в слово. Чем отличается, по экранам не видно',None)]),
]
sec=''
for n,(aid,name,verdict,ty,diff,main,extra,kids) in enumerate(APPS,1):
    mk,mu,md,_=main
    kl=''
    for k,t,u,d,idx in kids:
        f=figs(k,None if idx=='all' else idx,t) if idx else ''
        kl+=f'<li id="{k}"><b>{t}</b> · {link(u)}<br><span class="sub">{d}</span>'+(f'<div class="strip" style="margin-top:8px">{f}</div>' if f else '')+'</li>'
    sec+=(f'<section id="{aid}"><h2>{n}. {name}</h2><p class="sub">Вывод по рекламе: <b>{verdict}</b></p>'
          f'<p><b>Реклама (Tyver):</b> {ty}</p><p><b>Отличие от нашей воронки:</b> {diff}</p>'
          f'<h3>Главная воронка · {link(mu)}</h3><p class="sub">{md} · экранов: {len(files(mk))}</p>'+strip(figs(mk,None,name))+(ADS if extra=='ADS' else '')
          +(f'<h3>Другие воронки</h3><ul>{kl}</ul>' if kl else '')+'</section>')
rank=open(SP+'rank.html').read()
html=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Скрины воронок конкурентов</title><style>
:root{{color-scheme:light;--bg:#f7f7f5;--surface:#fff;--text:#191919;--text-2:#5f5f5f;--line:#e4e4e0;--accent:#257de0}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#121212;--surface:#1b1b1b;--text:#efefef;--text-2:#a2a2a2;--line:#2f2f2f;--accent:#5aa2f0}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#121212;--surface:#1b1b1b;--text:#efefef;--text-2:#a2a2a2;--line:#2f2f2f;--accent:#5aa2f0}}
html{{scroll-behavior:smooth}} section{{scroll-margin-top:12px}} h3{{scroll-margin-top:12px}} *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:28px 16px 48px}} h1{{font-size:24px;margin:0 0 6px}} .meta{{color:var(--text-2);font-size:13px;margin:0 0 8px}}
a{{color:var(--accent);overflow-wrap:anywhere}}
section{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;margin:16px 0}}
h2{{font-size:20px;margin:0 0 4px}} h3{{font-size:15px;margin:18px 0 2px}} .sub{{color:var(--text-2);font-size:13px;margin:0 0 10px}}
ul{{padding-left:20px}} li{{margin:4px 0}}
.strip{{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x proximity}}
figure{{margin:0;flex:0 0 200px;scroll-snap-align:start}} figure img{{width:200px;display:block;border-radius:10px;border:1px solid var(--line)}}
table{{border-collapse:collapse;font-size:14px;min-width:560px}} th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}} th{{color:var(--text-2);font-weight:600}}
.top{{position:fixed;right:16px;bottom:16px;width:48px;height:48px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.25);z-index:10}}
figcaption{{font-size:12px;color:var(--text-2);text-align:center;margin-top:4px}}
</style></head><body><main>
<h1>Скрины воронок конкурентов Robella</h1>
<p class="meta">Сняты 26.11.2026 автоматическим проходом: мобильный профиль iPhone, ответы — первые подходящие варианты, почта тестовая, оплату не делали. Ленты листаются вбок.</p>
{rank}{sec}{robsec}<a class="top" href="#rank" aria-label="Наверх к таблице" title="Наверх к таблице">↑</a></main></body></html>'''
open('reports/robella-competitor-funnels-screens-2026-11-26.html','w').write(html)
print(len(html)//1024,'KB')
