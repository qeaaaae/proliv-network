#!/bin/bash
# Usage: bash mask-nodes.sh fi|uk|de|ee|nl|kz
set -e
NODE=$1
mkdir -p /var/www/site
cp /var/www/site/index.html /var/www/site/index.html.bak 2>/dev/null || true

write_fi() {
cat > /var/www/site/index.html <<'EOF'
<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NordMetrics - Palvelun tila | Helsinki-klusteri</title>
<meta name="description" content="NordMetrics Oy:n palvelutilanne reaaliajassa: Helsinki-klusterin API, reititys, tallennus ja mittariputki. Käyttöaste, häiriöhistoria ja huoltoikkunat.">
<meta name="geo.region" content="FI-18">
<meta name="geo.placename" content="Helsinki">
<meta name="geo.position" content="60.1699;24.9384">
<meta name="ICBM" content="60.1699, 24.9384">
<meta name="geo.country" content="FI">
<meta property="og:type" content="website">
<meta property="og:locale" content="fi_FI">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:title" content="NordMetrics - Palvelun tila">
<meta property="og:site_name" content="NordMetrics Oy">
<style>
*{box-sizing:border-box;margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}
body{background:#f6f7f9;color:#23262b;min-height:100vh;padding-bottom:40px}
.top{background:#12326e;color:#fff;padding:18px 0}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
.top .wrap{display:flex;align-items:baseline;flex-wrap:wrap;gap:10px}
.brand{font-size:20px;font-weight:700;letter-spacing:.4px}
.brand em{font-style:normal;color:#8ab4f8}
.top .sub{color:#b9cdf0;font-size:13px;margin-left:auto}
nav a{color:#cfe0f7;font-size:13px;text-decoration:none;margin-left:16px}
.banner{margin:22px 0 18px;background:#e7f6ec;border:1px solid #bfe6ca;color:#1c6b35;border-radius:12px;padding:14px 18px;font-size:15px;display:flex;align-items:center;gap:10px}
.dot{width:11px;height:11px;border-radius:50%;background:#0f9d58;flex:none}
h2{font-size:17px;margin:26px 0 12px;color:#2b3242}
.card{background:#fff;border:1px solid #e3e5e9;border-radius:12px;padding:6px 20px}
.row{display:flex;justify-content:space-between;align-items:center;padding:11px 0;border-bottom:1px solid #f0f1f4;font-size:14.5px}
.row:last-child{border:none}
.svc{font-weight:500}
.svc small{display:block;color:#8a93a1;font-size:12px;font-weight:400;margin-top:1px}
.ok{color:#0f9d58;font-size:12.5px;font-weight:600}
.pill{background:#e7f6ec;padding:3px 10px;border-radius:12px;white-space:nowrap}
.pill.deg{background:#fdf3e0;color:#a36a00}
.bars{display:flex;gap:2px;margin-top:8px}
.bars i{flex:1;height:18px;border-radius:2px;background:#34a853}
.bars i.warn{background:#f4b400}
.legend{font-size:12px;color:#8a93a1;margin-top:6px;display:flex;justify-content:space-between}
.inc{background:#fff;border:1px solid #e3e5e9;border-radius:12px;padding:16px 20px;margin-bottom:12px}
.inc .d{font-size:12.5px;color:#8a93a1;margin-bottom:4px}
.inc b{font-size:14.5px;color:#2b3242}
.inc p{font-size:13.5px;color:#5a6270;line-height:1.55;margin-top:4px}
.stat{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stat div{background:#fff;border:1px solid #e3e5e9;border-radius:12px;padding:14px 18px}
.stat b{display:block;font-size:19px;color:#12326e}
.stat span{font-size:12px;color:#8a93a1}
.note{background:#eef3fb;border-left:3px solid #12326e;padding:13px 17px;border-radius:0 8px 8px 0;font-size:13.5px;line-height:1.6;color:#3d4a63;margin:10px 0 4px}
footer{margin-top:34px;color:#9aa1ad;font-size:12.5px;line-height:1.8;text-align:center}
footer a{color:#12326e;text-decoration:none}
</style>
</head>
<body>
<header class="top"><div class="wrap">
<span class="brand">Nord<em>Metrics</em></span>
<nav><a href="#palvelut">Palvelut</a><a href="#hairiot">Häiriöt</a><a href="#huolto">Huolto</a><a href="#tietoa">Tietoa</a></nav>
</div></header>
<div class="wrap">
<div class="banner"><span class="dot"></span>Kaikki järjestelmät toimivat normaalisti - päivitetty 21:52 UTC</div>

<div class="stat">
<div><b>99,97 %</b><span>käyttöaste 30 vrk</span></div>
<div><b>23 ms</b><span>mediaaniviive EU:n sisällä</span></div>
<div><b>3</b><span>datakeskusta: HEL1, HEL2, STO1</span></div>
<div><b>147 d</b><span>pisin häiriötön jakso tänä vuonna</span></div>
</div>

<h2 id="palvelut">Palvelukomponentit</h2>
<div class="card">
<div class="row"><span class="svc">API Gateway<small>api.nordmetrics.fi - REST ja WebSocket</small></span><span class="ok pill">Toiminnassa</span></div>
<div class="row"><span class="svc">Edge Router HEL1<small>Equinix HE1, Helsingin konesali</small></span><span class="ok pill">Toiminnassa</span></div>
<div class="row"><span class="svc">Edge Router HEL2<small>varmuuskapasiteetti, Espoo</small></span><span class="ok pill">Toiminnassa</span></div>
<div class="row"><span class="svc">Object Storage<small>S3-yhteensopiva, 3-replikointi</small></span><span class="ok pill">Toiminnassa</span></div>
<div class="row"><span class="svc">Metrics Pipeline<small>Prometheus etäkirjoitus + aggregaatio</small></span><span class="pill deg">Osittainen viive</span></div>
<div class="row"><span class="svc">Status Dashboard<small>tämä sivu + julkiset endpoinnit</small></span><span class="ok pill">Toiminnassa</span></div>
</div>

<h2>Käyttöaste, viimeiset 90 päivää</h2>
<div class="card" style="padding:16px 20px">
<div class="row"><span class="svc">API Gateway</span><span>99,99 %</span></div>
<div class="bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i class="warn"></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
<div class="legend"><span>90 pv sitten</span><span>tänään</span></div>
<div class="row" style="margin-top:10px"><span class="svc">Metrics Pipeline</span><span>99,91 %</span></div>
<div class="bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i class="warn"></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i class="warn"></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
<div class="legend"><span>90 pv sitten</span><span>tänään</span></div>
</div>

<h2 id="hairiot">Häiriöhistoria</h2>
<div class="inc"><div class="d">2.11.2026, 04:12-04:38 UTC - ratkaistu</div><b>Metrics Pipeline: kirjoitusviive kasvoi</b><p>Tallennusklusterin levy-i/o huippu aiheutti 8-12 s viivettä mittaridatassa. Kuorma tasattu lisäshardin avulla, data tallentui kokonaan ilman menetystä.</p></div>
<div class="inc"><div class="d">19.10.2026, 11:05-11:22 UTC - ratkaistu</div><b>HEL2-reititin: BGP-istunnon resetointi</b><p>Toimittajan ylläpidon yhteydessä yksi BGP-istunnoista päivittyi. Liikenne ohjautui HEL1:n kautta, asiakkaille ei näkynyttä katkoa.</p></div>
<div class="inc"><div class="d">30.9.2026, 14:40-14:47 UTC - ratkaistu</div><b>DNS-vastausten viiveet EU:ssa</b><p>Anycast-verkon välimuistin puhdistus aiheutti ohimenevän 60-90 ms lisäviiveen kyselyissä. Korjattu käynnistämällä resolverit uudelleen.</p></div>

<h2 id="huolto">Suunnitellut huollot</h2>
<div class="note"><b>Su 14.12.2026 klo 03:00-05:00 UTC:</b> HEL1-edge-routerin firmware-päivitys. Odotettavissa alle 30 s katko reitityksessä; liikenne ohjataan HEL2:een etukäteen. Mittariputken datassa ei katkoa.</div>
<div class="note"><b>La 20.12.2026 klo 02:00-04:00 UTC:</b> Object Storage -klusterin levyjen laajennus. Palvelu pysyy käytössä, kirjoitusviive voi nousta hetkellisesti.</div>

<h2 id="tietoa">Tietoa palvelusta</h2>
<div class="card" style="padding:16px 20px;font-size:14px;line-height:1.65;color:#4a5262">
<p>NordMetrics on suomalainen infrastruktuurin seuranta- ja tilastopalvelu, jonka ensisijainen klusteri sijaitsee Helsingissä. Päivitämme tämän sivun automaattisesti 60 sekunnin välein; tilatiedot haetaan suoraan tuotantopalvelimilta, ei välimuistista.</p>
<p style="margin-top:8px">Jos huomaat virheen, jota ei näy tällä sivulla, ilmoita osoitteeseen <b>status@nordmetrics.fi</b>. Voit myös tilata sähköposti-ilmoitukset häiriöistä - rekisteröinti avautuu samalla osoitteella aiheena "tilaus".</p>
</div>

<footer>
NordMetrics Oy - Mannerheimintie 12 B, 00100 Helsinki - Y-tunnus 2987654-3<br>
Kaikki ajat UTC. Tämä on julkinen tilasivu, ei sisällä asiakasdataa. - <a href="mailto:status@nordmetrics.fi">status@nordmetrics.fi</a>
</footer>
</div>
</body>
</html>

EOF
}

write_uk() {
cat > /var/www/site/index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BritByte Journal - Notes on self-hosting and small infrastructure</title>
<meta name="description" content="An independent UK weblog about self-hosting, home labs and running small infrastructure cheaply: backups, WireGuard, mail servers, monitoring and honest cost maths.">
<meta name="geo.region" content="GB-ENG">
<meta name="geo.placename" content="London">
<meta name="geo.position" content="51.5074;-0.1278">
<meta name="ICBM" content="51.5074, -0.1278">
<meta name="geo.country" content="GB">
<meta property="og:type" content="blog">
<meta property="og:locale" content="en_GB">
<meta property="og:locale:alternate" content="ru_RU">
<meta property="og:title" content="BritByte Journal">
<meta property="og:site_name" content="BritByte Journal">
<style>
*{box-sizing:border-box;margin:0;font-family:Georgia,'Times New Roman',serif}
body{background:#fdfcf8;color:#1f2330;min-height:100vh;padding:50px 24px}
.wrap{max-width:680px;margin:0 auto}
h1{font-size:30px;margin-bottom:6px}
.tag{color:#8a6d3b;font-size:13px;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px}
.about{font-size:14px;color:#6b6657;line-height:1.6;border-left:3px solid #d9d2bd;padding-left:16px;margin-bottom:38px}
article{margin-bottom:40px;padding-bottom:30px;border-bottom:1px solid #e5e0d5}
h2{font-size:21px;margin-bottom:8px}
.meta{color:#9a9585;font-size:13px;margin-bottom:12px}
p{color:#4a4f5c;font-size:15px;line-height:1.65;margin-bottom:12px}
p:last-child{margin-bottom:0}
a{color:#3d5a80;text-decoration:none}
a:hover{text-decoration:underline}
.kicker{font-size:12px;color:#b08d3e;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8px}
@media(max-width:620px){.cols{grid-template-columns:1fr}}
h3{font-size:15px;margin-bottom:10px;color:#1f2330}
.side ul{list-style:none}
.side li{font-size:13.5px;color:#5a5f6c;padding:5px 0;border-bottom:1px dashed #e5e0d5}
.side li:last-child{border:none}
.foot{color:#b5b0a0;font-size:12.5px;margin-top:34px;text-align:center;line-height:1.8}
</style>
</head>
<body>
<div class="wrap">
<h1>BritByte Journal</h1>
<div class="tag">Occasional notes on self-hosting - London</div>
<p class="about">A hobbyist's notebook about running your own services: what it actually costs, where the traps are, and when it is wiser to pay someone else. Written between two jobs and one temperamental fibre connection in south London.</p>

<article>
<div class="kicker">Storage</div>
<h2><a href="#">Why I moved my backups off S3</a></h2>
<div class="meta">2 November 2026 - 6 min read</div>
<p>After three years of paying for cold storage I finally sat down and did the maths. The result was mildly embarrassing: I was paying GBP 11.40 a month to keep 480 GB of backups that, in all that time, I had restored exactly twice - and one of those restores was a test.</p>
<p>The replacement is almost disappointingly boring: a used 4 TB drive in a USB enclosure at my parents' house in Kent, rsync over WireGuard every Sunday at 03:00, plus one local snapshot. Restore time went from "download overnight from eu-west-2" to "drive 40 minutes down the A2". The maths, the scripts and the honest failure modes are in this post.</p>
</article>

<article>
<div class="kicker">Networking</div>
<h2><a href="#">WireGuard on a five-year-old router</a></h2>
<div class="meta">19 October 2026 - 9 min read</div>
<p>An old TP-Link with OpenWrt still handles a full-tunnel setup just fine, if you keep the peer count low and resist the urge to route the entire house through it. My use case is narrower: phone and laptop back to home for the NAS, the printer and one security camera - around 3 Mbit/s steady, 25 Mbit/s burst.</p>
<p>Benchmarks inside: throughput versus MTU on VDSL2, why the default MTU was silently eating 20 percent of my line, and the firewall rules that keep the tunnel away from the rest of the LAN.</p>
</article>

<article>
<div class="kicker">Mail</div>
<h2><a href="#">Notes on running a small mail server in 2026</a></h2>
<div class="meta">30 September 2026 - 12 min read</div>
<p>Reputation management is still the hardest part, but the tooling has quietly got much better over the last two years. Postfix plus rspamd plus a strict SPF/DKIM/DMARC stack took one rainy Saturday; the last four months of outbound delivery land in inbox roughly 97 percent of the time.</p>
<p>The remaining 3 percent is almost entirely one large provider that shall remain nameless but rhymes with "outlook". I document the warmup schedule, the monitoring that catches blacklisting within the hour, and the point where I would just give up and buy hosted email.</p>
</article>

<article>
<div class="kicker">Monitoring</div>
<h2><a href="#">A sensible monitoring stack for a home lab</a></h2>
<div class="meta">8 September 2026 - 7 min read</div>
<p>Prometheus, one Raspberry Pi 4, and fourteen alert rules that have actually paged me. The trick was deleting the thirty that hadn't. Includes the exact alertmanager.yml I run and the one alert - "disk will fill within 7 days" - that has saved me twice.</p>
</article>

<article>
<div class="kicker">Costs</div>
<h2><a href="#">What a home lab really costs on UK tariffs</a></h2>
<div class="meta">22 August 2026 - 8 min read</div>
<p>Measured with a TP-Link smart plug over 90 days: the used ThinkCentre pulls 9 W idle, the NAS 14 W, the switch 4 W. At the October price cap that is about GBP 8.30 a month. The post covers the full spreadsheet, including the kit I should not have bought.</p>
</article>

<div class="cols">
<section class="side">
<h3>Archive</h3>
<ul>
<li><a href="#">November 2026</a> - backups off S3</li>
<li><a href="#">October 2026</a> - WireGuard, BGP jokes</li>
<li><a href="#">September 2026</a> - mail server, monitoring</li>
<li><a href="#">August 2026</a> - power costs, fans</li>
<li><a href="#">July 2026</a> - moving off Cloudflare</li>
<li><a href="#">June 2026</a> - ZFS on the NAS</li>
</ul>
</section>
<section class="side">
<h3>Elsewhere</h3>
<ul>
<li><a href="mailto:hello@britbyte.uk">hello@britbyte.uk</a> - corrections welcome</li>
<li><a href="#">RSS feed</a> - plain text, no tracking</li>
<li><a href="#">Reading list</a> - blogs I actually read</li>
<li><a href="#">Colophon</a> - how this site is served</li>
</ul>
</section>
</div>

<div class="foot">
BritByte Journal - written in London, hosted at home - an independent weblog since 2021.<br>
No analytics, no cookies, no comments section on purpose.
</div>
</div>
</body>
</html>

EOF
}

write_de() {
cat > /var/www/site/index.html <<'EOF'
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KursTicker - Marktdaten aus Frankfurt | DAX, Devisen, Rohstoffe</title>
<meta name="description" content="Tägliche Marktübersicht aus Frankfurt: DAX-Werte, Weltindizes, Devisen und Rohstoffe mit 15-minütiger Verzögerung. Kompakt, ohne Anmeldung, ohne Tracking.">
<meta name="geo.region" content="DE-HE">
<meta name="geo.placename" content="Frankfurt am Main">
<meta name="geo.position" content="50.1109;8.6821">
<meta name="ICBM" content="50.1109, 8.6821">
<meta name="geo.country" content="DE">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:title" content="KursTicker - Marktdaten">
<meta property="og:site_name" content="KursTicker GmbH">
<style>
*{box-sizing:border-box;margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}
body{background:#101418;color:#dbe2ea;min-height:100vh;padding:36px 20px 46px}
.wrap{max-width:720px;margin:0 auto}
h1{font-size:24px;color:#f0b429;margin-bottom:4px}
.sub{color:#7d8794;font-size:14px;margin-bottom:8px}
nav{margin-bottom:24px;font-size:13px}
nav a{color:#8ab4f8;text-decoration:none;margin-right:16px}
h2{font-size:16px;color:#aebacb;margin:26px 0 10px;font-weight:600}
table{width:100%;border-collapse:collapse;background:#161b21;border-radius:10px;overflow:hidden}
th{font-size:11.5px;color:#7d8794;text-transform:uppercase;text-align:left;padding:11px 16px;border-bottom:1px solid #242b33;letter-spacing:.5px}
td{padding:11px 16px;border-bottom:1px solid #1d232b;font-size:14.5px}
tr:last-child td{border:none}
td.num{text-align:right;font-variant-numeric:tabular-nums}
td:first-child{font-weight:500}
td small{display:block;color:#67707d;font-size:11.5px;font-weight:400}
.up{color:#3fb950}.down{color:#f85149}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:640px){.grid2{grid-template-columns:1fr}}
.news{background:#161b21;border-radius:10px;padding:6px 18px}
.news div{padding:11px 0;border-bottom:1px solid #1d232b;font-size:14px;line-height:1.5}
.news div:last-child{border:none}
.news .t{color:#f0b429;font-size:12px;margin-right:8px;font-variant-numeric:tabular-nums}
.box{background:#181f28;border-left:3px solid #f0b429;border-radius:0 8px 8px 0;padding:14px 18px;font-size:13px;line-height:1.6;color:#98a3b2;margin-top:22px}
.foot{color:#5d6672;font-size:12px;margin-top:26px;text-align:center;line-height:1.8}
</style>
</head>
<body>
<div class="wrap">
<h1>KursTicker</h1>
<div class="sub">Marktdaten - Frankfurt - Stand 21:52 CET - verzögert um 15 Min.</div>
<nav><a href="#dax">DAX</a><a href="#indizes">Indizes</a><a href="#devisen">Devisen</a><a href="#rohstoffe">Rohstoffe</a><a href="#news">Nachrichten</a></nav>

<h2 id="dax">DAX - Auswahl</h2>
<table>
<tr><th>Wert</th><th>Kurs (EUR)</th><th style="text-align:right">1 Tag</th></tr>
<tr><td>DAX-Index<small>XETRA, Perf.</small></td><td class="num">19 842,11</td><td class="num up">+0,62%</td></tr>
<tr><td>SAP SE<small>716460</small></td><td class="num">221,40</td><td class="num up">+0,44%</td></tr>
<tr><td>Siemens AG<small>723610</small></td><td class="num">172,18</td><td class="num down">-0,31%</td></tr>
<tr><td>Allianz SE<small>840400</small></td><td class="num">294,65</td><td class="num up">+0,88%</td></tr>
<tr><td>Airbus SE<small>938914</small></td><td class="num">156,32</td><td class="num down">-0,17%</td></tr>
<tr><td>Deutsche Telekom<small>555750</small></td><td class="num">29,84</td><td class="num up">+0,23%</td></tr>
<tr><td>Münchener Rück<small>843002</small></td><td class="num">486,20</td><td class="num up">+1,02%</td></tr>
<tr><td>BASF SE<small>BASF11</small></td><td class="num">43,71</td><td class="num down">-0,74%</td></tr>
<tr><td>Infineon<small>623100</small></td><td class="num">31,55</td><td class="num up">+1,35%</td></tr>
<tr><td>RWE AG<small>703712</small></td><td class="num">32,09</td><td class="num down">-0,52%</td></tr>
</table>

<div class="grid2">
<div>
<h2 id="indizes">Weltindizes</h2>
<table>
<tr><th>Index</th><th>Stand</th><th style="text-align:right">1 Tag</th></tr>
<tr><td>EuroStoxx 50</td><td class="num">4 928,4</td><td class="num up">+0,55%</td></tr>
<tr><td>S&amp;P 500</td><td class="num">5 971,2</td><td class="num up">+0,31%</td></tr>
<tr><td>Nasdaq 100</td><td class="num">21 244,7</td><td class="num down">-0,12%</td></tr>
<tr><td>FTSE 100</td><td class="num">8 302,6</td><td class="num up">+0,18%</td></tr>
<tr><td>Nikkei 225</td><td class="num">39 214,0</td><td class="num down">-0,44%</td></tr>
</table>
</div>
<div>
<h2 id="devisen">Devisen &amp; Krypto</h2>
<table>
<tr><th>Paar</th><th>Kurs</th><th style="text-align:right">1 Tag</th></tr>
<tr><td>EUR/USD</td><td class="num">1,0812</td><td class="num down">-0,14%</td></tr>
<tr><td>EUR/GBP</td><td class="num">0,8473</td><td class="num up">+0,06%</td></tr>
<tr><td>EUR/CHF</td><td class="num">0,9391</td><td class="num up">+0,11%</td></tr>
<tr><td>BTC/EUR</td><td class="num">68 410</td><td class="num up">+1,87%</td></tr>
<tr><td>ETH/EUR</td><td class="num">2 614</td><td class="num up">+2,41%</td></tr>
</table>
</div>
</div>

<h2 id="rohstoffe">Rohstoffe</h2>
<table>
<tr><th>Rohstoff</th><th>Kurs</th><th style="text-align:right">1 Tag</th></tr>
<tr><td>Gold (USD/Feinunze)</td><td class="num">2 718,30</td><td class="num up">+0,42%</td></tr>
<tr><td>Brent Öl (USD/Barrel)</td><td class="num">73,86</td><td class="num down">-1,08%</td></tr>
<tr><td>Erdgas TTF (EUR/MWh)</td><td class="num">46,12</td><td class="num up">+2,90%</td></tr>
<tr><td>Kupfer (USD/Tonne)</td><td class="num">9 142,0</td><td class="num up">+0,61%</td></tr>
<tr><td>Weizen (EUR/Tonne, Euronext)</td><td class="num">218,75</td><td class="num down">-0,32%</td></tr>
</table>

<h2 id="news">Marktnotizen</h2>
<div class="news">
<div><span class="t">21:15</span>DAX schliesst über 19 800 Punkten - Impulse von Halbleitern und Versicherungen.</div>
<div><span class="t">19:40</span>EZB-Ratsmitglied: Inflationspfad stabil, Dezember-Entscheid bleibt datenabhängig.</div>
<div><span class="t">17:55</span>Erdgas TTF legt zu - kälterer November lässt Speicherstände schneller sinken.</div>
<div><span class="t">15:20</span>SAP übernimmt US-Analytics-Anbieter - Analysten sehen Synergien über Plan.</div>
<div><span class="t">13:05</span>Bundesanleihe 10j. bei 2,31% - Rendite weitgehend seitwärts.</div>
</div>

<div class="box"><b>Hinweis:</b> Alle Kurse mit 15 Minuten Verzögerung, Quelle: Konsolidierte Kursfeeds XETRA/Eurex sowie OTC-Mittelkurse. Diese Seite dient ausschliesslich der Information und stellt keine Anlage-, Rechts- oder Steuerberatung dar. Für Handelsentscheidungen nutzen Sie die Echtzeitdaten Ihres Brokers.</div>

<div class="foot">
KursTicker GmbH - Neue Mainzer Strasse 52, 60311 Frankfurt am Main - <a href="mailto:redaktion@kursticker.de" style="color:#8ab4f8">redaktion@kursticker.de</a><br>
Handelsregister Frankfurt HRB 118 402 - Datenstand wie angezeigt, keine Gewähr.
</div>
</div>
</body>
</html>

EOF
}

write_ee() {
cat > /var/www/site/index.html <<'EOF'
<!DOCTYPE html>
<html lang="et">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pildiraam - Tallinna fotoateljee | Portreed, pulmad, linnavaated</title>
<meta name="description" content="Pildiraam OÜ on Tallinna vanalinnas tegutsev fotoateljee: portree- ja pulmapildistamine, äripildid, linnatuurid. Hinnakiri, lahtiolekuajad ja broneerimine.">
<meta name="geo.region" content="EE-37">
<meta name="geo.placename" content="Tallinn">
<meta name="geo.position" content="59.4370;24.7536">
<meta name="ICBM" content="59.4370, 24.7536">
<meta name="geo.country" content="EE">
<meta property="og:type" content="website">
<meta property="og:locale" content="et_EE">
<meta property="og:locale:alternate" content="ru_RU">
<meta property="og:title" content="Pildiraam - Tallinna fotoateljee">
<meta property="og:site_name" content="Pildiraam OÜ">
<style>
*{box-sizing:border-box;margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}
body{background:#f4f1ec;color:#2a2a28;min-height:100vh;padding-bottom:40px}
.top{background:#3d4a3a;color:#f0ede4;padding:16px 0}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
.top .wrap{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px}
.brand{font-size:22px;font-weight:700;letter-spacing:.4px}
.brand em{font-style:normal;color:#d8c07a}
nav{margin-left:auto}
nav a{color:#d4dccb;font-size:13px;text-decoration:none;margin-left:16px}
.hero{padding:34px 0 8px}
h1{font-size:26px;margin-bottom:8px}
.lead{color:#6b6759;font-size:15px;line-height:1.6;max-width:600px}
h2{font-size:18px;margin:30px 0 14px;color:#3d4a3a}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
@media(max-width:600px){.grid{grid-template-columns:repeat(2,1fr)}}
.ph{aspect-ratio:4/3;border-radius:10px;display:flex;align-items:flex-end;padding:10px;color:#fff;font-size:12.5px;font-weight:500}
.ph:nth-child(8n+1){background:linear-gradient(135deg,#c9bfae,#8f9ba8)}
.ph:nth-child(8n+2){background:linear-gradient(135deg,#9db5a0,#6b7f75)}
.ph:nth-child(8n+3){background:linear-gradient(135deg,#a8b8c9,#5f6f85)}
.ph:nth-child(8n+4){background:linear-gradient(135deg,#c9a8a8,#8a6a6a)}
.ph:nth-child(8n+5){background:linear-gradient(135deg,#b5a8c9,#6f6085)}
.ph:nth-child(8n+6){background:linear-gradient(135deg,#a8c9bd,#5f857a)}
.ph:nth-child(8n+7){background:linear-gradient(135deg,#c9b8a0,#8a7862)}
.ph:nth-child(8n+8){background:linear-gradient(135deg,#9fa8c9,#5d6685)}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgb(60 50 30 / 8%)}
th{font-size:11.5px;color:#8a8577;text-align:left;padding:11px 16px;border-bottom:1px solid #e8e4da;text-transform:uppercase;letter-spacing:.5px}
td{padding:12px 16px;border-bottom:1px solid #efece4;font-size:14.5px;vertical-align:top}
tr:last-child td{border:none}
td small{display:block;color:#8a8577;font-size:12px;margin-top:2px}
td:last-child{white-space:nowrap;font-weight:600}
.rev{background:#fff;border-radius:12px;padding:16px 20px;margin-bottom:12px;box-shadow:0 1px 4px rgb(60 50 30 / 8%)}
.rev p{font-size:14px;line-height:1.6;color:#4d4a40}
.rev .who{font-size:12.5px;color:#8a8577;margin-top:6px}
.info{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:600px){.info{grid-template-columns:1fr}}
.info div{background:#fff;border-radius:12px;padding:16px 20px;box-shadow:0 1px 4px rgb(60 50 30 / 8%)}
.info b{display:block;font-size:14px;margin-bottom:8px;color:#3d4a3a}
.info p,.info li{font-size:13.5px;line-height:1.65;color:#5a564a}
.info li{margin-left:16px}
.note{background:#e6ecdf;border-left:3px solid #6b7f5a;border-radius:0 8px 8px 0;padding:14px 18px;font-size:13.5px;line-height:1.6;color:#4a5344;margin-top:14px}
footer{margin-top:34px;text-align:center;color:#a39e8e;font-size:12.5px;line-height:1.8}
footer a{color:#3d4a3a;text-decoration:none}
</style>
</head>
<body>
<header class="top"><div class="wrap">
<span class="brand">Pildi<em>raam</em></span>
<nav><a href="#teenused">Teenused</a><a href="#galerii">Galerii</a><a href="#hinnad">Hinnakiri</a><a href="#kontakt">Kontakt</a></nav>
</div></header>
<div class="wrap">
<div class="hero">
<h1>Fotoateljee Tallinna vanalinnas</h1>
<p class="lead">Pildiraam tegutseb 2019. aastast Pärnu maantee ääres, vanalinna serval. Pildistame portreesid, pulmi, äripilte ja linna - stuudios ja plenaaris. Vastame päeva jooksul, enamasti paari tunni jooksul.</p>
</div>

<h2 id="galerii">Viimaste hooaegade valik</h2>
<div class="grid">
<div class="ph">Raekoja plats, hommik</div><div class="ph">Toompea vaated</div><div class="ph">Kalamaja tänavad</div>
<div class="ph">Pirita rand</div><div class="ph">Telliskivi hoovid</div><div class="ph">Kadrioru park</div>
<div class="ph">Viru väravad</div><div class="ph">Noblessner sadam</div>
</div>

<h2 id="teenused">Teenused</h2>
<table>
<tr><th>Teenus</th><th>Sisaldab</th><th>Hind</th></tr>
<tr><td>Portree stuudios</td><td>1 tund, 15 retušeeritud kaadrit<small>sobilik CV-le, LinkedInile, kingituseks</small></td><td>45 EUR</td></tr>
<tr><td>Pere / paar plenaaris</td><td>1,5 tundi vanalinnas või Kadriorus<small>kuni 30 töödeldud kaadrit</small></td><td>120 EUR</td></tr>
<tr><td>Pulmapäev</td><td>8 tundi, 400+ kaadrit, veebigalerii<small>lisatud koosolek ja ajaplaan</small></td><td>890 EUR</td></tr>
<tr><td>Äripildid tiimile</td><td>3-10 inimest, ühtne stiil<small>kohapeal või stuudios, 2 tööpäeva</small></td><td>240 EUR-st</td></tr>
<tr><td>Linnatuur + pildistus</td><td>2 tundi jalutuskäigu ja piltidega<small>turistidele, kuni 4 inimest</small></td><td>150 EUR</td></tr>
<tr><td>Tootepildistus</td><td>valgustelk, 10-20 eset<small>e-poe jaoks, valge või elustiili taust</small></td><td>leppe kokku</td></tr>
</table>

<h2>Kliendi tagasiside</h2>
<div class="rev"><p>"Broneerisime perepildi Kadriorgu - fotograaf tuli täpsele kohale, valgus tabas kuldset tundi. Kaadrid saime 4 päevaga, kõik rahul."</p><div class="who">- Maris K., Tallinn</div></div>
<div class="rev"><p>"Firma 8 inimese portreed tehti ühe hommikuga, stiil on ühtne ja inimlik. Järgmine kord tuleme tootepiltidega."</p><div class="who">- Andres, Nortal</div></div>
<div class="rev"><p>"Pulmapildistus vanalinnas: rahulik, kiire, häid juhiseid. Vanemate perekonnaalbum on lemmik kingitus."</p><div class="who">- Liisa ja Karl</div></div>

<h2 id="kontakt">Broneerimine ja külastamine</h2>
<div class="info">
<div><b>Kontakt</b>
<p>Pärnu mnt 27, 10141 Tallinn<br>stuudio@pildiraam.ee<br>+372 5123 4488 (ka WhatsApp)</p>
<p style="margin-top:8px">Vastame E-R 10-19, L pärast kokkulepet.<br>Eesti ja inglise keeles, vene keeles e-postis.</p>
</div>
<div><b>Broneerimine</b>
<ul>
<li>Vali teenus ja saada kuupäev e-postiga</li>
<li>Kinnitame 24 h jooksul + saadame ettemaksu 20%</li>
<li>Stuudios tasuta parkla Pärnu mnt taga</li>
<li>Töötlemata eelvaated 48 h, valmiskaadrid 4-7 päeva</li>
</ul>
</div>
</div>
<div class="note"><b>Külalisele:</b> Kui oled Tallinnas lühikest aega - "linnatur + pildistus" mahub ühte hommikusse. Tee ring Raekoja plats - Kohtuotsa - Kadriorg ja saad hooaja pildid kaasa.</div>

<footer>
Pildiraam OÜ - reg 14578921 - Pärnu mnt 27, 10141 Tallinn - <a href="mailto:stuudio@pildiraam.ee">stuudio@pildiraam.ee</a><br>
&copy; 2019-2026 Pildiraam. Kaadrid on autori omad, privaatsed klienditööd ei avaldata.
</footer>
</div>
</body>
</html>

EOF
}

write_nl() {
cat > /var/www/site/index.html <<'EOF'
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FleurExpo - Amsterdamse bloemenveiling | Dagelijkse klokveiling</title>
<meta name="description" content="FleurExpo organiseert dagelijkse klokveilingen van snijbloemen en potplanten in Amsterdam-Noord. Lopende kavels, dagkoersen, informatie voor kopers en bezoekers.">
<meta name="geo.region" content="NL-NH">
<meta name="geo.placename" content="Amsterdam">
<meta name="geo.position" content="52.3676;4.9041">
<meta name="ICBM" content="52.3676, 4.9041">
<meta name="geo.country" content="NL">
<meta property="og:type" content="website">
<meta property="og:locale" content="nl_NL">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:title" content="FleurExpo - Amsterdamse bloemenveiling">
<meta property="og:site_name" content="FleurExpo BV">
<style>
*{box-sizing:border-box;margin:0;font-family:Georgia,'Times New Roman',serif}
body{background:#faf7f2;color:#2b2620;min-height:100vh}
.top{background:#20462f;color:#f4efe4;padding:14px 0}
.wrap{max-width:960px;margin:0 auto;padding:0 20px}
.top .wrap{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap}
.logo{font-size:20px;font-weight:bold;letter-spacing:.5px}
.logo span{color:#f5b942}
nav a{color:#d8e6d0;text-decoration:none;margin-left:18px;font-size:13px;font-family:Verdana,sans-serif}
.hero{padding:40px 0 30px;border-bottom:1px solid #e7dfd0}
.hero h1{font-size:30px;font-weight:normal;margin-bottom:8px}
.hero p{color:#6d6659;max-width:620px;line-height:1.55;font-size:15px}
.clock{font-family:Verdana,sans-serif;background:#20462f;color:#f5b942;display:inline-block;padding:8px 16px;border-radius:4px;margin-top:18px;font-size:14px}
h2{font-size:18px;border-bottom:2px solid #20462f;padding-bottom:6px;margin:30px 0 14px;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.lot{background:#fff;border:1px solid #e7dfd0;border-radius:8px;padding:16px;display:flex;gap:14px}
.sw{width:46px;height:46px;border-radius:50%;flex:none}
.lot h3{font-size:15.5px;margin-bottom:4px}
.lot .meta{color:#8a8272;font-size:12px;font-family:Verdana,sans-serif}
.price{font-family:Verdana,sans-serif;margin-top:8px;font-size:14.5px}
.price b{color:#20462f}
.tt{width:100%;border-collapse:collapse;font-size:13px;font-family:Verdana,sans-serif;background:#fff;border:1px solid #e7dfd0;border-radius:8px;overflow:hidden}
.tt td,.tt th{padding:8px 12px;border-bottom:1px solid #efe9dc;text-align:left}
.tt th{color:#8a8272;font-weight:normal;font-size:11px;text-transform:uppercase}
.tt tr:last-child td{border:none}
.up{color:#1d7a3a}.dn{color:#b3392e}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media(max-width:700px){.cols{grid-template-columns:1fr}}
.info{background:#fff;border:1px solid #e7dfd0;border-radius:8px;padding:18px 20px;font-family:Verdana,sans-serif;font-size:13.5px;line-height:1.7;color:#4d463c}
.info li{margin-left:18px;margin-bottom:6px}
.note{background:#f0e9db;border-left:3px solid #f5b942;padding:14px 18px;font-size:13px;line-height:1.5;color:#5d564a;margin:8px 0 4px}
.foot{background:#20462f;color:#b9cbb1;padding:26px 0;margin-top:40px;font-size:12px;font-family:Verdana,sans-serif;line-height:1.9}
.foot a{color:#e8f0df}
</style>
</head>
<body>
<header class="top"><div class="wrap">
<div class="logo">Fleur<span>Expo</span></div>
<nav><a href="#veiling">Veiling</a><a href="#lots">Kavels</a><a href="#koersen">Koersen</a><a href="#kopers">Voor kopers</a><a href="#contact">Contact</a></nav>
</div></header>

<section class="hero"><div class="wrap">
<h1 id="veiling">Veilingklok van vandaag</h1>
<p>Dagelijkse klokveiling van snijbloemen, potplanten en seizoensproducten uit Westland, Aalsmeer en de Bollenstreek. Inschrijving voor kopers vanaf 05:30, eerste gong om 06:00 CET. Locaties: Amsterdam-Noord, Aalsmeer en Naaldwijk.</p>
<div class="clock">Gong 06:00 CET - Kavel 1 - Tulipa 'Strong Gold'</div>
</div></section>

<div class="wrap">
<div class="note" style="margin-top:18px">Let op: vanwege het stormweer van afgelopen nacht kan de aanvoer van partijen uit Westland tot 30 minuten vertraagd zijn. Controleer de lotstatus voor het bieden.</div>

<h2 id="lots">Lopende kavels</h2>
<div class="grid">
<div class="lot"><div class="sw" style="background:#e8a13d"></div><div><h3>Tulipa 'Strong Gold'</h3><div class="meta">Kavel 1 - 400 stelen - A1 - 60cm</div><div class="price">EUR 0,42 /steel <b class="up">+3%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#c94f6d"></div><div><h3>Rosa 'Sweet Avalanche'</h3><div class="meta">Kavel 2 - 250 stelen - A2 - 50cm</div><div class="price">EUR 0,61 /steel <b class="dn">-1%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#7d5ba6"></div><div><h3>Lathyrus 'Winter Sunshine'</h3><div class="meta">Kavel 3 - 180 bossen - B1 - 45cm</div><div class="price">EUR 1,10 /bos <b class="up">+6%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#4f86c6"></div><div><h3>Delphinium 'Volkerfrieden'</h3><div class="meta">Kavel 4 - 220 stelen - A1 - 80cm</div><div class="price">EUR 0,88 /steel <b>-</b></div></div></div>
<div class="lot"><div class="sw" style="background:#5fa777"></div><div><h3>Monstera deliciosa 17cm</h3><div class="meta">Kavel 5 - 96 potten - kwekerij Sion</div><div class="price">EUR 7,40 /pot <b class="dn">-2%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#d95f43"></div><div><h3>Gerbera 'Pasta Rosata'</h3><div class="meta">Kavel 6 - 500 stelen - A1 - 55cm</div><div class="price">EUR 0,35 /steel <b class="up">+4%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#e86f8f"></div><div><h3>Paeonia 'Sarah Bernhardt'</h3><div class="meta">Kavel 7 - 320 stelen - A1 - 55cm</div><div class="price">EUR 0,92 /steel <b class="up">+8%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#f2e14c"></div><div><h3>Helianthus 'Sunrich Orange'</h3><div class="meta">Kavel 8 - 300 stelen - B1 - 70cm</div><div class="price">EUR 0,55 /steel <b>-</b></div></div></div>
<div class="lot"><div class="sw" style="background:#8fbf6f"></div><div><h3>Ficus lyrata 21cm</h3><div class="meta">Kavel 9 - 64 potten - kwekerij Vreugdenhil</div><div class="price">EUR 12,80 /pot <b class="up">+2%</b></div></div></div>
<div class="lot"><div class="sw" style="background:#b9d7ea"></div><div><h3>Matthiola 'Iron Marine'</h3><div class="meta">Kavel 10 - 260 bossen - A2 - 60cm</div><div class="price">EUR 0,78 /bos <b class="dn">-3%</b></div></div></div>
</div>

<h2 id="koersen">Dagkoersen (gemiddeld van deze veiling)</h2>
<table class="tt">
<tr><th>Productgroep</th><th>Gem. prijs</th><th>t.o.v. vrijdag</th><th>Aanbod</th></tr>
<tr><td>Tulpen</td><td>EUR 0,44 /steel</td><td class="up">+2,1%</td><td>normaal</td></tr>
<tr><td>Rozen</td><td>EUR 0,58 /steel</td><td class="dn">-0,8%</td><td>ruim</td></tr>
<tr><td>Pioenen</td><td>EUR 0,90 /steel</td><td class="up">+7,4%</td><td>krap</td></tr>
<tr><td>Groenpotplanten</td><td>EUR 9,10 /pot</td><td class="dn">-1,5%</td><td>normaal</td></tr>
<tr><td>Seizoensmix</td><td>EUR 1,35 /bos</td><td class="up">+1,2%</td><td>normaal</td></tr>
</table>

<h2 id="kopers">Voor kopers</h2>
<div class="cols">
<div class="info"><b style="display:block;margin-bottom:8px;color:#20462f">Registratie en bieden</b>
<li>Kopersnummer aanvragen via veiling@fleurexpo.nl - KvK-uittreksel en legitimatie vereist.</li>
<li>Bieden kan ter plaatse in de veilingzaal (stoel + knop), via de kopersapp of remote via livestream.</li>
<li>Veilinggeld 3,5% over de klokprijs; minimale transactie EUR 40.</li>
<li>Afhalen tot 10:30 bij het expeditiedock, koeltransport op aanvraag.</li>
</div>
<div class="info"><b style="display:block;margin-bottom:8px;color:#20462f">Bezoekers</b>
<li>Veilingzaal te bezoeken ma-vr 06:00-10:00 met kopers- of gastenkaart (EUR 7,50).</li>
<li>Rondleiding voor groepen vanaf 8 personen op reservering, incl. uitleg kloksysteem.</li>
<li>Adres zaal: Overschiestraat 184, Amsterdam-Noord - gratis parkeren aan de deur.</li>
<li>Openingstijden kantoor: ma-vr 08:30-17:00, za gesloten.</li>
</div>
</div>

<h2>Veilingnieuws</h2>
<table class="tt">
<tr><th>Tijd</th><th>Bericht</th></tr>
<tr><td>07:42</td><td>Kavel 12 (Freesia 'Ambassador') uitgesteld naar morgen</td></tr>
<tr><td>07:15</td><td>Gemiddelde klokprijs tulp +2,1% t.o.v. vrijdag</td></tr>
<tr><td>06:58</td><td>Nieuwe koper geregistreerd: BloemImport Lier BV</td></tr>
<tr><td>06:30</td><td>Aanvoer Naaldwijk hersteld na wegwerkzaamheden</td></tr>
<tr><td>06:00</td><td>Eerste gong - veiling geopend</td></tr>
</table>

<h2>Over FleurExpo</h2>
<div class="info">FleurExpo is een onafhankelijke klokveiling in Amsterdam-Noord, opgericht in 1987 als alternatief voor de grote cooperaties. We veilen dagelijks circa 1400 kavels van 90 kwekers voor bloemisten, groothandelaren en exporteurs uit Noordwest-Europa. Het bedrijf telt 34 medewerkers en draait op zonne-energie en een eigen koelcentrale.</div>
</div>

<footer class="foot"><div class="wrap" id="contact">
FleurExpo BV - Overschiestraat 184, 1062 XK Amsterdam - kvk 34.21.77.09 - <a href="mailto:veiling@fleurexpo.nl">veiling@fleurexpo.nl</a> - +31 20 555 0184<br><br>
&copy; 2026 FleurExpo. Prijzen excl. veilinggeld en btw. Kloktijden: ma-vr 06:00-09:30 CET.
</div></footer>
</body>
</html>

EOF
}

write_kz() {
cat > /var/www/site/index.html <<'EOF'
<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bozjyra - Маңғыстау саяхат гиді | Ақтау, Бозжыра, Шерқала</title>
<meta name="description" content="Маңғыстауға тәуелсіз сапар жоспары: Бозжыра төбесі, Шерқала тауы, Торық шарлар аңғары, Ақтау жағажайы. Қашықтықтар, мезгіл, бағалар, жол жай-күйі және кеңестер.">
<meta name="keywords" content="Бозжыра, Маңғыстау, Ақтау, саяхат, Қазақстан, Каспий, Шерқала, Торық, Үстірт, гид, бағыттар">
<meta name="language" content="Kazakh">
<meta name="geo.region" content="KZ-31">
<meta name="geo.placename" content="Ақтау, Маңғыстау облысы">
<meta name="geo.position" content="43.6427;51.1983">
<meta name="ICBM" content="43.6427, 51.1983">
<meta name="geo.country" content="KZ">
<meta name="DC.language" content="kk">
<meta name="DC.coverage" content="Маңғыстау облысы, Қазақстан">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Bozjyra.kz">
<meta property="og:locale" content="kk_KZ">
<meta property="og:locale:alternate" content="ru_RU">
<meta property="og:title" content="Bozjyra - Маңғыстау саяхат гиді">
<meta property="og:description" content="Бозжыра, Шерқала, Торық және Ақтау: нақты бағыттар, қашықтықтар, мезгіл кестесі және жол кеңестері.">
<meta property="og:url" content="https://kz.proliv-network.xyz/">
<link rel="canonical" href="https://kz.proliv-network.xyz/">
<style>
*{box-sizing:border-box;margin:0}
body{background:#eef1ee;color:#20261f;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;min-height:100vh}
.serif{font-family:Georgia,'Times New Roman',serif}
.wrap{max-width:860px;margin:0 auto;padding:0 22px}
header{padding:26px 0 0;display:flex;align-items:baseline;flex-wrap:wrap;gap:8px}
.brand{font-family:Georgia,serif;font-size:24px;font-weight:700;color:#14595b;letter-spacing:.5px}
.brand em{font-style:normal;color:#c98b2d}
nav{margin-left:auto}
nav a{color:#5c665f;text-decoration:none;font-size:13px;margin-left:16px}
nav a:hover{color:#14595b}
.hero{padding:34px 0 6px}
.hero svg{width:100%;height:auto;display:block;border-radius:14px;margin-top:22px}
h1{font-size:30px;font-weight:700;line-height:1.22;max-width:640px;margin-bottom:12px}
.lead{color:#4d564f;font-size:16px;line-height:1.65;max-width:620px}
.ru-note{margin-top:16px;font-size:13.5px;line-height:1.55;color:#6b6f68;background:#e2e8e2;border-left:3px solid #c98b2d;padding:12px 16px;border-radius:0 8px 8px 0;max-width:620px}
section{padding:24px 0}
h2{font-size:19px;color:#14595b;margin-bottom:14px;font-family:Georgia,serif}
h3{font-size:15.5px;color:#26312b;margin:16px 0 6px}
table.routes{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgb(20 40 35 / 8%)}
.routes th{font-size:11.5px;color:#8a9088;text-align:left;padding:11px 16px;border-bottom:1px solid #e4e7e2;text-transform:uppercase;letter-spacing:.6px}
.routes td{padding:12px 16px;border-bottom:1px solid #eef0ec;font-size:14.5px;vertical-align:top}
.routes tr:last-child td{border-bottom:none}
.routes td:first-child{font-weight:600;color:#26312b}
.km{color:#5c665f;white-space:nowrap}
.note-sm{font-size:12.5px;color:#8a9088;display:block;margin-top:3px}
.season{background:#fff;border-radius:12px;padding:6px 20px;box-shadow:0 1px 4px rgb(20 40 35 / 8%)}
.season div{padding:11px 0;border-bottom:1px solid #eef0ec;font-size:14.5px;line-height:1.55}
.season div:last-child{border:none}
.season b{color:#14595b}
.card{background:#fff;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgb(20 40 35 / 8%);font-size:14.5px;line-height:1.7;color:#3d453f}
.card p+p{margin-top:8px}
.tips{font-size:14.5px;line-height:1.7;color:#3d453f;background:#fff;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgb(20 40 35 / 8%)}
.tips li{margin-left:18px;margin-bottom:8px}
.faq dt{font-weight:600;color:#26312b;padding:12px 0 4px;font-size:14.5px}
.faq dd{font-size:14px;line-height:1.6;color:#4d564f;padding-bottom:10px;border-bottom:1px solid #e8ebe6}
.faq dd:last-child{border:none}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.fact{background:#fff;border-radius:12px;padding:14px 18px;box-shadow:0 1px 4px rgb(20 40 35 / 8%)}
.fact b{display:block;font-family:Georgia,serif;font-size:20px;color:#14595b;margin-bottom:2px}
.fact span{font-size:12.5px;color:#6b6f68;line-height:1.4;display:block}
footer{padding:26px 0 40px;color:#7a8178;font-size:12.5px;line-height:1.7}
footer a{color:#14595b;text-decoration:none}
</style>
</head>
<body>
<div class="wrap">
<header>
  <span class="brand">Bozjyra<em>.kz</em></span>
  <nav><a href="#bagyttar">Бағыттар</a><a href="#mezgin">Мезгілі</a><a href="#aqtau">Ақтау</a><a href="#kenges">Кеңестер</a><a href="#faq">Сұрақтар</a></nav>
</header>

<div class="hero">
<h1 class="serif">Бозжыра, Шерқала, Торық: Маңғыстаудың ақ тасты еліне сапар жоспары</h1>
<p class="lead">Маңғыстау - Қазақстанның ең сюрреалистік жері: меловой каньондар, шар тәрізді жыралар және Каспий жағажайы. Бұл гидте - Ақтаудан басталатын нақты бағыттар, қашықтықтар, маусым бойынша ескертпелер және жол кеңестері.</p>
<div class="ru-note">Коротко по-русски: Бозжыра - меловой каньон в ~300 км от Актау, главная точка Мангистау. Лучшее время - апрель-май и сентябрь-октябрь, летом до +40. Дорога местами грунтовая, нужен полный привод или тур из Актау на 1-2 дня. Ниже маршруты, сезоны, советы и ответы на частые вопросы.</div>
<svg viewBox="0 0 860 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Бозжыра меловой жыралары">
<rect width="860" height="180" rx="14" fill="#dfe9e6"/>
<path d="M0 150 L80 150 L110 92 L150 92 L178 118 L210 118 L238 70 L290 70 L318 108 L352 108 L380 88 L430 88 L462 128 L500 128 L536 60 L600 60 L632 116 L668 116 L700 96 L760 96 L800 132 L860 132 L860 180 L0 180 Z" fill="#f4efe4" stroke="#c9bfa5" stroke-width="1.5"/>
<path d="M110 92 L150 92 L178 118 L210 118 M238 70 L290 70 L318 108 M536 60 L600 60 L632 116" fill="none" stroke="#b3a88c" stroke-width="1" opacity=".7"/>
<circle cx="760" cy="42" r="20" fill="#f0c96e" opacity=".85"/>
<path d="M0 156 L860 156" stroke="#cfc5ab" stroke-width="1" opacity=".6"/>
<text x="26" y="164" font-family="Georgia,serif" font-size="13" fill="#8a8270">Бозжыра жотасы - көрініс биіктік нүктесінен</text>
</svg>
</div>

<section>
<h2>Бозжыра деген не</h2>
<div class="card">
<p>Бозжыра - Үстірт үстіртінің солтүстік жағасындағы меловой жыралар мен каньондар жүйесі, Маңғыстаудың басты көрнекі жері. Ақ кирпіш тәрізді шоқылар биіктігі 200 метрге дейін жетеді, төменгі бақылау нүктесінен көрініс шаңырақты қалаға ұқсайды. Аумағы Каспий маңының ұлттық табиғи паркінің құрамына кіреді.</p>
<p>Жақын маңда: Шерқала тауы ("асылханның сарайы" тәрізді жеке тау), Торық аңғарындағы шар тәрізді конкрециялар, Ұлы шоқы тауы және Ұстюрт маңының жыралары. Көшпелі жауһарлар: антилопа-сайгақ, дала тасбақасы, қыран құс.</p>
</div>
</section>

<section id="bagyttar">
<h2>Негізгі бағыттар Ақтаудан</h2>
<table class="routes">
<tr><th>Нүкте</th><th>Қашықтық</th><th>Жолда</th><th>Ұсынылатын уақыт</th></tr>
<tr><td>Бозжыра төбесі<span class="note-sm">бақылау нүктесі + төменгі каньон</span></td><td class="km">~300 км</td><td>4-5 сағ</td><td>таңертең немесе күн батысы</td></tr>
<tr><td>Шерқала тауы<span class="note-sm">жеке тау, көне бекініс орны</span></td><td class="km">~170 км</td><td>2-2,5 сағ</td><td>таңғы сағаттер</td></tr>
<tr><td>Торық - шарлар аңғары<span class="note-sm">конкрециялар, диаметрі 3-4 м</span></td><td class="km">~250 км</td><td>3,5-4 сағ</td><td>таң және кешкі жарық</td></tr>
<tr><td>Ұлы шоқы тауы<span class="note-sm">Үстірт үстіртінің ең биік нүктесі</span></td><td class="km">~280 км</td><td>4 сағ</td><td>күндіз</td></tr>
<tr><td>Тұзбайır тұзды көлі<span class="note-sm">құрғақ тұзды алап, фотогеник</span></td><td class="km">~180 км</td><td>2,5-3 сағ</td><td>күндіз</td></tr>
<tr><td>Ақтау жағажайы<span class="note-sm">сквер, жар, Каспий толқындары</span></td><td class="km">қала ішінде</td><td>-</td><td>кешкі серуен</td></tr>
</table>
</section>

<section id="mezgin">
<h2>Қашан бару керек</h2>
<div class="season">
<div><b>Сәуір - мамыр:</b> ең жақсы мезгілі - дала гүлдейді, ауа +18-28°С, жұмсақ жарық фотоға жақсы.</div>
<div><b>Маусым - тамыз:</b> ыстық, +35-42°С; шығуды таңғы 5-ке жоспарлау керек, күндізге толық су қоры.</div>
<div><b>Қыркүйек - қазан:</b> екінші жақсы мезгілі - +20-30°С, ашық ауа, адам аз.</div>
<div><b>Қараша - наурыз:</b> салқын және желді, грунт жолдар жауыннан кейін уақытша жабылады.</div>
</div>
</section>

<section id="aqtau">
<h2>Ақтау қаласы - негізгі ақпарат</h2>
<div class="facts">
<div class="fact"><b>~200 мың</b><span>тұрғын саны, Маңғыстау облысының орталығы</span></div>
<div class="fact"><b>UTC+5</b><span>уақыт белдеуі, қысқа қыс немесе жеңіл жаз жоқ</span></div>
<div class="fact"><b>₸ теңге</b><span>валюта; карталар барлық жерде жүреді, далаға ақша алу ұсынылады</span></div>
<div class="fact"><b>112</b><span>бірыңғай төтенше нөмір; полиция 102, тез көмек 103</span></div>
</div>
<div class="card" style="margin-top:14px">
<p>Қала 1963 жылы Каспий портının маңында салынған. Әуежайдан қалаға такси Yandex Go / inDriver қосымшаларымен ~3500-5000 ₸. Орталықта жағажай бойымен сквер, кафелер, базар және кеме айлағы бар - сапар алдындағы соңғы цивилизация нүктесі.</p>
</div>
</section>

<section id="kenges">
<h2>Пайдалы кеңестер</h2>
<ul class="tips">
<li>Көлік: Ақтауға ұшақ (Москва/Алматы/Астана рейстері күн сайын), далаға - тек 4x4. Грунт учаскесінің соңғы 40-60 км-і жауыннан кейін өтпейді.</li>
<li>Тур: жеке гидімен 1 күндік Бозжыра + Шерқала шамамен 45-60 мың ₸/көлік, 2 күндік толық шолу 90-120 мың ₸.</li>
<li>Су мен отын: жолда дүкен жоқ - адамға кем 3 л су, толық бак, запас дөңгелек және компрессор.</li>
<li>Байланыс: Ақтаудан 60 км кейін талсып жүреді - офлайн картаны (Organic Maps / OsmAnd) алдын ала жүктеңіз.</li>
<li>Түнеме: төбеде шатырмен түнеме рұқсат; желді ескеріп якорьларды мықтап қадау керек.</li>
<li>Жол жай-күйі: Ақтау - Шетпе тас жолы жақсы, Шетпеден кейін грунт. Жауыннан кейін кемінде 1 күн кептіру керек.</li>
</ul>
</section>

<section id="faq">
<h2>Жиі қойылатын сұрақтар</h2>
<dl class="faq">
<dt>Шетелдікке виза керек пе?</dt>
<dd>Көптеген елдердің азаматтары Қазақстанға 30 күнге дейін визасыз кіре алады. Нақты ережені сапар алдында өтініш беретін елдің консулдығы немесе ҚР СІМ сайтынан тексеріңіз.</dd>
<dt>Бозжыраға қанша күн керек?</dt>
<dd>Бозжыраға - бір толық күн (жол+жүру). Шерқала мен Торық тағы бір күн алады. Жай сапарға 3-4 күн жоспарлаған дұрыс.</dd>
<dt>Ауыз су бар ма?</dt>
<dd>Далада тұрақты ауыз су көзі жоқ - барлық суды өзіңізбен алыңыз. Шетпе ауылында ақырғы дүкендер бар.</dd>
<dt>Балалармен баруға бола ма?</dt>
<dd>Болады, бірақ ұзақ жол мен ыстық ескеріңіз. Кішкентай баламен түнемеден гөри 1 күндік тур оңайырақ.</dd>
<dt>Ең жақсы фото нүктесі қайсы?</dt>
<dd>Жоғарғы бақылау нүктесінен күн батысы - "айдаһар мойны" жотасы; төменгі каньонда - таңғы бұлттар арасындағы жыралар.</dd>
</dl>
</section>

<footer>
Bozjyra.kz - тәуелсіз саяхат гиді · Ақтау, Маңғыстау облысы, Қазақстан · Байланыс: <a href="mailto:hello@bozjyra.kz">hello@bozjyra.kz</a><br>
Материалдар - авторлық жеке жоба, 2021-2026. Сапар алдында жол мен ауа райын ресми көздерден тексеріңіз.
</footer>
</div>
</body>
</html>
EOF
}

case "$NODE" in
  fi) write_fi ;; uk) write_uk ;; de) write_de ;; ee) write_ee ;; nl) write_nl ;; kz) write_kz ;;
  *) echo "unknown node"; exit 1 ;;
esac

nginx -t && systemctl reload nginx

# пинги офф + fail2ban
iptables -C INPUT -p icmp --icmp-type echo-request -j DROP 2>/dev/null || iptables -I INPUT -p icmp --icmp-type echo-request -j DROP
command -v fail2ban-server >/dev/null || apt-get install -y -qq fail2ban >/dev/null 2>&1 || true
systemctl enable --now fail2ban >/dev/null 2>&1 || true
curl -sk "https://127.0.0.1:8443/" -o /dev/null -w "mask8443: %{http_code}\n" || true
echo "$NODE mask deployed"
