#!/usr/bin/env python3
"""今日は何の日スキルの計算スクリプト(Python標準ライブラリのみ)。

  python nanohi.py today [--date YYYY-MM-DD]                 その日の祝日・行事・記念日
  python nanohi.py next [--date YYYY-MM-DD] [--days 30]      これから来る祝日・行事
  python nanohi.py range --from YYYY-MM-DD --to YYYY-MM-DD   期間の休日と連休(土日・祝日)
  python nanohi.py check                                     自己点検

祝日は2022年以降の法律に基づいて計算する(春分・秋分は1980〜2099年の近似式。振替休日・国民の休日も)。
年中行事・制定された記念日は、根拠のはっきりしたものだけを入れた小さな一覧(日付ごとの網羅はしない)。
占いスキル(koyomi.py)が近くにあれば、節分・二十四節気の入り・冬至・夏至・土用の丑・十五夜・十三夜も出す。
文章(一言・話題の広げ方)は呼び出し側のAIが書く。
"""
import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEEK = "月火水木金土日"

# (月, 日, 名前, 種類, 説明, 行事食)。日付が固定のもの
FIXED = [
    (1, 1, "元日", "祝日", "年の初めを祝う日(国民の祝日に関する法律)", ["おせち", "雑煮"]),
    (1, 7, "人日の節句(七草)", "年中行事", "七草粥を食べて一年の無病息災を願う五節句の一つ", ["七草粥"]),
    (1, 11, "鏡開き", "年中行事", "お正月に供えた鏡餅を下ろして食べる", ["お汁粉"]),
    (1, 17, "防災とボランティアの日", "記念日", "阪神・淡路大震災(1995年)を忘れず、防災とボランティア活動の大切さを考える日(政府が制定)", []),
    (2, 11, "建国記念の日", "祝日", "建国をしのび、国を愛する心を養う日(国民の祝日に関する法律)", []),
    (2, 23, "天皇誕生日", "祝日", "天皇の誕生日を祝う日(国民の祝日に関する法律)", []),
    (3, 3, "桃の節句(上巳)", "年中行事", "女の子の健やかな成長を願うひな祭り。五節句の一つ", ["ちらし寿司", "はまぐりのお吸い物"]),
    (3, 8, "国際女性デー", "国際デー", "国連が定めた、女性の権利と平等を考える日", []),
    (4, 22, "アースデー(地球の日)", "国際デー", "地球環境を考える日として世界各地で行われる", []),
    (4, 23, "子ども読書の日", "記念日", "子どもの読書活動の推進に関する法律(2001年)で定められた日", []),
    (4, 29, "昭和の日", "祝日", "激動の昭和を顧み、国の将来に思いをいたす日(国民の祝日に関する法律)", []),
    (5, 3, "憲法記念日", "祝日", "日本国憲法の施行(1947年)を記念する日", []),
    (5, 4, "みどりの日", "祝日", "自然に親しみ、その恩恵に感謝する日", []),
    (5, 5, "こどもの日(端午の節句)", "祝日", "子どもの人格を重んじ、母に感謝する日。端午の節句でもある", ["柏餅", "ちまき"]),
    (5, 31, "世界禁煙デー", "国際デー", "世界保健機関(WHO)が定めた、たばこの害を考える日", []),
    (6, 5, "世界環境デー", "国際デー", "国連が定めた、環境保全を考える日", []),
    (6, 10, "時の記念日", "記念日", "671年に水時計(漏刻)で時を知らせたという日本書紀の記述にちなみ、1920年に制定", []),
    (7, 7, "七夕", "年中行事", "短冊に願いを書く五節句の一つ", ["そうめん"]),
    (8, 11, "山の日", "祝日", "山に親しむ機会を得て、山の恩恵に感謝する日(2016年から)", []),
    (8, 15, "終戦記念日", "記念日", "全国戦没者追悼式が行われ、戦没者を追悼し平和を祈念する日(1982年に閣議決定)", []),
    (9, 1, "防災の日", "記念日", "関東大震災(1923年)の日にちなみ、1960年に閣議了解で制定", []),
    (9, 9, "重陽の節句", "年中行事", "菊を愛で長寿を願う五節句の一つ", ["栗ご飯", "菊の酢の物"]),
    (9, 21, "国際平和デー", "国際デー", "国連が定めた、停戦と非暴力を呼びかける日", []),
    (10, 1, "コーヒーの日", "記念日", "日本のコーヒー業界が1983年に定めた日(新年度の始まりにちなむ)", []),
    (10, 14, "鉄道の日", "記念日", "1872年(明治5年)10月14日(旧暦9月12日)の新橋〜横浜の鉄道開業にちなみ、1994年に制定", []),
    (10, 16, "世界食料デー", "国際デー", "国連食糧農業機関(FAO)の設立を記念し、食料問題を考える日", []),
    (11, 3, "文化の日", "祝日", "自由と平和を愛し、文化をすすめる日(国民の祝日に関する法律)", []),
    (11, 20, "世界こどもの日", "国際デー", "国連が定めた、子どもの権利を考える日", []),
    (11, 23, "勤労感謝の日", "祝日", "勤労をたっとび、生産を祝い、国民が互いに感謝する日", []),
    (12, 1, "世界エイズデー", "国際デー", "WHOが定めた、エイズへの理解を深める日", []),
    (12, 10, "世界人権デー", "国際デー", "1948年の世界人権宣言の採択にちなむ国連の日", []),
    (12, 31, "大晦日", "年中行事", "一年の最後の日。年越しそばを食べる風習がある", ["年越しそば"]),
]
LAW_FIXED = {(m, d): n for m, d, n, k, *_ in FIXED if k == "祝日"}
HAPPY_MONDAY = {1: (2, "成人の日", "おとなになったことを自覚し、自ら生き抜こうとする青年を祝いはげます日"),
                7: (3, "海の日", "海の恩恵に感謝し、海洋国日本の繁栄を願う日"),
                9: (3, "敬老の日", "多年にわたり社会につくしてきた老人を敬愛し、長寿を祝う日"),
                10: (2, "スポーツの日", "スポーツを楽しみ、他者を尊重する精神を培う日")}



def date_arg(text):
    """argparse用: 日付の指定ミスを日本語で知らせる。"""
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError("日付は YYYY-MM-DD の形で、実在する日を指定してください(入力: %s)" % text)


def equinox(year, spring):
    base = 20.8431 if spring else 23.2488
    return int(base + 0.242194 * (year - 1980) - int((year - 1980) / 4))


def nth_monday(year, month, n):
    d = datetime.date(year, month, 1)
    first = d + datetime.timedelta(days=(0 - d.weekday()) % 7)
    return first + datetime.timedelta(weeks=n - 1)


def holidays(year):
    if year < 1980 or year > 2099:
        raise ValueError("祝日の計算は1980〜2099年に対応しています(春分・秋分の近似式の範囲)。2022年より前は当時の法律と異なる場合があります")
    """その年の祝日 {date: 名前}。2022年以降の法に基づく(国民の休日・振替休日を含む)。"""
    h = {}
    for (m, d), name in LAW_FIXED.items():
        h[datetime.date(year, m, d)] = name
    for m, (n, name, _) in HAPPY_MONDAY.items():
        h[nth_monday(year, m, n)] = name
    h[datetime.date(year, 3, equinox(year, True))] = "春分の日"
    h[datetime.date(year, 9, equinox(year, False))] = "秋分の日"
    base = dict(h)
    day = datetime.date(year, 1, 2)
    while day.year == year:   # 国民の休日(前日と翌日がともに祝日の平日)
        if day not in h and day.weekday() != 6 and \
                (day - datetime.timedelta(days=1)) in base and (day + datetime.timedelta(days=1)) in base:
            h[day] = "国民の休日"
        day += datetime.timedelta(days=1)
    for d in sorted(base):    # 振替休日(祝日が日曜なら、次の祝日でない日)
        if d.weekday() == 6:
            nxt = d + datetime.timedelta(days=1)
            while nxt in h:
                nxt += datetime.timedelta(days=1)
            h[nxt] = "振替休日"
    return h


def holiday_name(d):
    return holidays(d.year).get(d)


def is_off(d):
    return d.weekday() >= 5 or holiday_name(d) is not None


def _koyomi_module():
    home = os.path.expanduser("~")
    for p in (os.path.join(HERE, "..", "..", "占い", "scripts"),
              os.path.join(home, ".claude", "skills", "占い", "scripts"),
              os.path.join(home, ".gemini", "skills", "占い", "scripts"),
              os.path.join(home, ".agents", "skills", "占い", "scripts")):
        if os.path.exists(os.path.join(p, "koyomi.py")):
            sys.path.insert(0, p)
            try:
                import koyomi
                return koyomi
            except Exception:
                return None
            finally:
                sys.path.remove(p)
    return None


def events_on(d, koyomi=None):
    """その日の行事・記念日の一覧。"""
    ev = []
    name = holiday_name(d)
    law = LAW_FIXED.get((d.month, d.day))
    if name and not law:
        desc = HAPPY_MONDAY.get(d.month, (0, "", ""))[2] if name == HAPPY_MONDAY.get(d.month, (0, ""))[1] else ""
        if name == "春分の日":
            desc = "自然をたたえ、生物をいつくしむ日"
        elif name == "秋分の日":
            desc = "祖先をうやまい、なくなった人々をしのぶ日"
        elif name == "振替休日":
            desc = "祝日が日曜日の時、その次の日が休みになる"
        elif name == "国民の休日":
            desc = "前日と翌日が祝日の平日が休みになる"
        ev.append({"名前": name, "種類": "祝日", "説明": desc, "行事食": []})
    for m, dd, n, kind, desc, food in FIXED:
        if (m, dd) == (d.month, d.day):
            ev.append({"名前": n, "種類": kind, "説明": desc, "行事食": food})
    for spring, label, food in ((True, "春", ["ぼたもち"]), (False, "秋", ["おはぎ"])):
        mid = datetime.date(d.year, 3 if spring else 9, equinox(d.year, spring))
        diff = (d - mid).days
        if abs(diff) <= 3:
            ev.append({"名前": "%sのお彼岸" % label, "種類": "年中行事",
                       "説明": "春分・秋分の前後3日ずつの7日間。先祖を供養する(%s)" % (
                           "彼岸の入り" if diff == -3 else "彼岸明け" if diff == 3 else "中日" if diff == 0 else "期間中"),
                       "行事食": food})
    if koyomi:
        nm, hit = koyomi.sekki_of(d)
        if hit:
            ev.append({"名前": "%sの日(二十四節気)" % nm, "種類": "二十四節気", "説明": "二十四節気の%sに入る日" % nm,
                       "行事食": ["かぼちゃ料理"] if nm == "冬至" else []})
        nxt, hit2 = koyomi.sekki_of(d + datetime.timedelta(days=1))
        if hit2 and nxt == "立春":
            ev.append({"名前": "節分", "種類": "年中行事", "説明": "立春の前日。豆まきで邪気を払う", "行事食": ["恵方巻", "福豆", "いわし"]})
        notes = koyomi.koyomi(d)["特別な日"] + koyomi.other_notes(d)
        if any("土用の丑の日" in x for x in notes):
            ev.append({"名前": "土用の丑の日", "種類": "年中行事", "説明": "夏の土用の丑の日。うなぎを食べる風習", "行事食": ["うなぎ"]})
        m, day, leap = koyomi.kyureki(d)
        if not leap and (m, day) == (8, 15):
            ev.append({"名前": "十五夜(中秋の名月)", "種類": "年中行事", "説明": "旧暦8月15日の月見。団子やすすきを供える", "行事食": ["月見団子", "里芋"]})
        if not leap and (m, day) == (9, 13):
            ev.append({"名前": "十三夜", "種類": "年中行事", "説明": "旧暦9月13日の月見。栗や豆を供えるので「栗名月」とも", "行事食": ["栗ご飯"]})
    elif (d.month, d.day) == (2, 3):
        ev.append({"名前": "節分(目安)", "種類": "年中行事", "説明": "立春の前日(年により2/2〜2/4)。豆まきで邪気を払う", "行事食": ["恵方巻", "福豆"]})
    return ev


def cmd_today(args):
    d = args.date
    k = _koyomi_module()
    ev = events_on(d, k)
    out = {"日付": d.isoformat(), "曜日": WEEK[d.weekday()], "休日": is_off(d),
           "祝日": holiday_name(d), "行事": ev, "暦の精度": "暦計算あり" if k else "暦計算なし(占いスキル無し)"}
    if d.year < 2022:
        out["注"] = "2022年より前は、当時の法律と祝日が異なる場合があります"
    foods = sorted({f for e in ev for f in e["行事食"]})
    if foods:
        out["行事食"] = foods
    if not ev:
        out["案内"] = "この日の登録された行事・記念日はありません。日付ごとの一覧は網羅していません"
    return out


def upcoming(day, days):
    k = _koyomi_module()
    res = []
    for i in range(1, days + 1):
        d = day + datetime.timedelta(days=i)
        for e in events_on(d, k):
            if e["種類"] in ("祝日", "年中行事"):
                res.append({"日付": d.isoformat(), "曜日": WEEK[d.weekday()], "あと日数": i, "名前": e["名前"],
                            "種類": e["種類"]})
    return res


def cmd_next(args):
    return {"今日": args.date.isoformat(), "範囲": "%d日以内" % args.days,
            "行事": upcoming(args.date, args.days)}


def cmd_range(args):
    if args.start > args.end:
        raise ValueError("開始日が終了日より後になっています")
    """期間内の休日(土日・祝日)と、連休(土日祝が続く日の並び)。2日以上の並びだけ。"""
    runs, cur = [], []
    day = args.start
    while day <= args.end + datetime.timedelta(days=0):
        if is_off(day):
            cur.append(day)
        else:
            if len(cur) >= 2:
                runs.append(cur)
            cur = []
        day += datetime.timedelta(days=1)
    if len(cur) >= 2:
        runs.append(cur)
    out = []
    for r in runs:
        hol = [holiday_name(x) for x in r if holiday_name(x)]
        out.append({"開始": r[0].isoformat(), "終了": r[-1].isoformat(), "日数": len(r),
                    "曜日": WEEK[r[0].weekday()] + "〜" + WEEK[r[-1].weekday()], "祝日": hol})
    return {"期間": "%s〜%s" % (args.start, args.end), "連休(2日以上)": out,
            "注": "期間の端で連休が途切れる場合は、前後の日付も含めて見直してください"}


def cmd_check(args):
    d = datetime.date
    cases = [
        (holidays(2026).get(d(2026, 3, 20)) == "春分の日", "2026年の春分の日は3/20"),
        (holidays(2026).get(d(2026, 9, 23)) == "秋分の日", "2026年の秋分の日は9/23"),
        (holidays(2026).get(d(2026, 9, 22)) == "国民の休日", "2026年9/22は国民の休日(敬老の日と秋分の日の間)"),
        (holidays(2026).get(d(2026, 10, 12)) == "スポーツの日", "2026年のスポーツの日は10/12"),
        (holidays(2026).get(d(2026, 7, 20)) == "海の日", "2026年の海の日は7/20"),
        (holidays(2025).get(d(2025, 2, 24)) == "振替休日", "2025年2/24は振替休日(天皇誕生日が日曜)"),
        (holidays(2024).get(d(2024, 5, 6)) == "振替休日", "2024年5/6は振替休日"),
        (holidays(2026).get(d(2026, 5, 6)) == "振替休日", "2026年5/6は振替休日(憲法記念日が日曜)"),
        (len(holidays(2026)) == 18, "2026年の祝日は18日(振替休日・国民の休日を含む)"),
        (nth_monday(2026, 1, 2) == d(2026, 1, 12), "2026年の成人の日は1/12"),
        (any(e["名前"] == "鉄道の日" for e in events_on(d(2026, 10, 14))), "10/14は鉄道の日"),
        (any("お彼岸" in e["名前"] and "中日" in e["説明"] for e in events_on(d(2026, 9, 23))), "秋分の日はお彼岸の中日"),
    ]
    for good, label in cases:
        print(("OK  " if good else "NG  ") + label)
    sys.exit(0 if all(g for g, _ in cases) else 1)



# --- ページ(HTML)の書き出し(形だけの初版。見た目の磨きは後日) ---
def _page_escape(x):
    import html
    return html.escape(str(x))


def render_page(data, skill_name, tpl_path):
    """AIが組み立てた内容(JSON)をHTMLページにする。
    内容の形: {"日付": "…", "副題": "…", "一言": "…", "注記": "…",
              "節": [{"題": "…", "行": [["題","文"],…]} | {"題": "…", "本文": "…"} | {"題": "…", "棒": [["名","値の文",0〜100],…]}]}"""
    e = _page_escape
    secs = []
    for s in data.get("節", []):
        body = ""
        if s.get("行"):
            body += '<dl class="rows">%s</dl>' % "".join(
                '<div class="row"><dt>%s</dt><span class="leader"></span><dd>%s</dd></div>' % (e(a), e(b)) for a, b in s["行"])
        if s.get("本文"):
            body += "".join('<p class="para">%s</p>' % e(p) for p in str(s["本文"]).split("\n") if p.strip())
        if s.get("棒"):
            body += '<ul class="bars">%s</ul>' % "".join(
                '<li class="bar"><span>%s</span><span class="track"><span class="fill" style="width:%d%%"></span></span><span class="val">%s</span></li>'
                % (e(n), max(0, min(100, int(v))), e(t)) for n, t, v in s["棒"])
        secs.append('<section class="sec"><h2>%s</h2>%s</section>' % (e(s.get("題", "")), body))
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()
    vals = {"日付": e(data.get("日付", "")),
            "副題": ('<p class="sub">%s</p>' % e(data["副題"])) if data.get("副題") else "",
            "一言": ('<p class="lead">%s</p>' % e(data["一言"])) if data.get("一言") else "",
            "節": "\n  ".join(secs),
            "注記": ('<p class="note">%s</p>' % e(data["注記"])) if data.get("注記") else ""}
    for k, v in vals.items():
        tpl = tpl.replace("{{%s}}" % k, v)
    return tpl


def cmd_page(args):
    import json as _json
    from pathlib import Path as _Path
    here = _Path(os.path.dirname(os.path.abspath(__file__)))
    data = _json.loads(_Path(args.データ).read_text(encoding="utf-8"))
    _Path(args.out).write_text(render_page(data, "今日は何の日", str(here / "page.html")), encoding="utf-8")
    return {"書き出し": args.out}


def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    _pg = sub.add_parser("page", help="内容(JSON)をHTMLページ(Artifact用)に書き出す")
    _pg.add_argument("--データ", required=True, help="あなた(AI)が組み立てた内容のJSONファイル")
    _pg.add_argument("--out", required=True, help="書き出すHTMLのパス")
    _pg.set_defaults(fn=cmd_page)
    to_date = date_arg
    p = sub.add_parser("today")
    p.add_argument("--date", type=to_date, default=datetime.date.today())
    p.set_defaults(fn=cmd_today)
    p = sub.add_parser("next")
    p.add_argument("--date", type=to_date, default=datetime.date.today())
    p.add_argument("--days", type=int, default=30)
    p.set_defaults(fn=cmd_next)
    p = sub.add_parser("range")
    p.add_argument("--from", dest="start", type=to_date, required=True)
    p.add_argument("--to", dest="end", type=to_date, required=True)
    p.set_defaults(fn=cmd_range)
    p = sub.add_parser("check")
    p.set_defaults(fn=cmd_check)
    args = ap.parse_args()
    try:
        print(json.dumps(args.fn(args), ensure_ascii=False, indent=2))
    except ValueError as e:
        print(json.dumps({"エラー": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
