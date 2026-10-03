"""سنجمان - ۴ داشبورد ممیزی و کشف تقلب پارکینگ (Streamlit)
اجرا: streamlit run app.py   |  فایل‌های کنار هم: app.py, logo.jpg, parking_fraud_dataset.xlsx, .streamlit/config.toml
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="سنجمان | پایش پارکینگ", page_icon="▦", layout="wide")
HERE = Path(__file__).parent

# ------------------------------------------------------------ پالت (استخراج‌شده از لوگو)
SLATE, DEEP, SURF = "#455E62", "#2C4144", "#365054"
YEL, MINT, TEAL, GRN, CORAL = "#FFE08A", "#88CFC0", "#4FC0A8", "#1BB08E", "#FF8A7A"
TXT, SUB = "#F1F7F5", "#B5CCC8"
ACC = {1: YEL, 2: MINT, 3: TEAL, 4: GRN}
STATE_C = {"ok": GRN, "warn": YEL, "bad": CORAL}

st.markdown(f"""<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
html,body,.stApp,button,input,textarea,select,[data-testid="stSidebar"]{{font-family:'Vazirmatn',system-ui,sans-serif!important}}
.stApp,.block-container,[data-testid="stSidebar"]{{direction:rtl;text-align:right}}
.stApp{{background:{DEEP};color:{TXT}}}
header[data-testid="stHeader"],footer,#MainMenu{{display:none}}
.block-container{{padding-top:1rem;max-width:1450px}}
[data-testid="stSidebar"]{{background:{SLATE};border-left:1px solid rgba(255,255,255,.08)}}
[data-testid="stVerticalBlockBorderWrapper"]{{background:{SURF};border:1px solid rgba(255,255,255,.08)!important;border-radius:22px!important}}
.ban{{--ac:{YEL};display:grid;grid-template-columns:1.1fr 1.4fr;gap:18px;background:linear-gradient(120deg,{SLATE},{SURF});
 border:1px solid rgba(255,255,255,.1);border-radius:28px;padding:22px 26px;margin-bottom:16px;position:relative;overflow:hidden}}
.ban::before{{content:'';position:absolute;inset:0 auto 0 0;width:8px;background:var(--ac)}}
.ban h1{{font-size:1.55rem;margin:0 0 10px;font-weight:800}}
.ban .bm span{{display:inline-block;background:rgba(255,255,255,.08);border-radius:999px;padding:4px 12px;margin:0 0 6px 8px;font-size:.78rem;color:{SUB}}}
.ban .bm b{{color:var(--ac)}}
.vd i{{font-style:normal;font-size:.75rem;color:var(--ac);font-weight:700}}
.vd p{{margin:4px 0 0;font-size:1.05rem;line-height:1.9}} .vd p b{{color:var(--ac);font-weight:800}}
.kpi{{--ac:{TEAL};background:{SURF};border:1px solid rgba(255,255,255,.08);border-radius:22px;padding:14px 18px;height:100%}}
.kpi .kl{{color:{SUB};font-size:.8rem;display:block}} .kpi b{{font-size:1.5rem;font-weight:700;display:block;margin:4px 0}}
.kpi .kh{{font-size:.74rem;color:{SUB};display:inline-flex;align-items:center;gap:6px}}
.kpi .kh::before{{content:'';width:8px;height:8px;border-radius:50%;background:var(--sc,{GRN})}}
.kpi.hero{{background:linear-gradient(135deg,{SLATE},{SURF});border:2px solid var(--ac);box-shadow:0 0 0 4px rgba(255,255,255,.03);padding:20px 24px}}
.kpi.hero .kl{{color:var(--ac);font-weight:700;font-size:.92rem}} .kpi.hero b{{font-size:2.7rem;font-weight:800;color:{TXT}}}
.ct{{font-weight:700;font-size:.98rem}} .cs{{color:{SUB};font-size:.78rem;margin-bottom:6px}}
.note{{background:rgba(255,224,138,.1);border:1px dashed {YEL};border-radius:14px;padding:8px 14px;font-size:.78rem;color:{YEL};margin:6px 0}}
.alert{{border-radius:18px;padding:12px 18px;font-weight:600;margin-bottom:12px}}
.alert.bad{{background:rgba(255,138,122,.15);border:1px solid {CORAL};color:{CORAL}}}
.alert.ok{{background:rgba(27,176,142,.15);border:1px solid {GRN};color:{MINT}}}
.eq{{background:{SURF};border-radius:20px;padding:14px 16px;border:1px solid rgba(255,255,255,.08)}}
.eq h4{{margin:0 0 8px;font-size:1rem}} .chip{{display:inline-block;border-radius:999px;padding:3px 10px;margin:2px;font-size:.74rem;font-weight:600}}
.chip.ok{{background:rgba(27,176,142,.2);color:{MINT}}} .chip.bad{{background:rgba(255,138,122,.2);color:{CORAL}}}
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------ تعاریف
FLAGS = {  # فلگ: (عنوان، دسته کلان، وزن)
    "Flag_Void_After_Exit": ("ابطال پس از خروج", "مالی و پوز", 40), "Flag_POS_Invalid": ("پوز نامعتبر/بدون RRN", "مالی و پوز", 35),
    "Flag_Overcharge": ("اضافه‌دریافتی", "مالی و پوز", 25), "Flag_Underpay": ("کم‌ثبتی نقد", "مالی و پوز", 25),
    "Flag_Manual_Edit_HighConf": ("ویرایش پلاک با OCR بالا", "پلاک و فیش", 30), "Flag_Ticket_Swap": ("تعویض فیش رسوبی", "پلاک و فیش", 40),
    "Flag_Passback": ("نقض توالی تردد", "پلاک و فیش", 30), "Flag_Lost_Suspicious": ("مفقودی مشکوک", "پلاک و فیش", 30),
    "Flag_Tailgating": ("قطار ماشین", "گیت و راهبند", 30), "Flag_Barrier_Keep_Open": ("باز نگه‌داشتن راهبند", "گیت و راهبند", 25),
    "Flag_Wrong_Direction": ("تردد خلاف جهت", "گیت و راهبند", 30), "Flag_Camera_Drop": ("قطعی دوربین", "گیت و راهبند", 15),
    "Flag_Time_Drift": ("انحراف ساعت گیت", "گیت و راهبند", 30), "Flag_Exempt_NoWhitelist": ("معافیت غیرمجاز", "تخفیف و فرجه", 35),
    "Flag_Discount_Reuse": ("تکرار بن تخفیف", "تخفیف و فرجه", 25), "Flag_Ghost_Occupancy": ("خودروی رسوبی نامرئی", "رسوبی", 15),
}
FL = list(FLAGS)
DOMAINS = ["مالی و پوز", "پلاک و فیش", "گیت و راهبند", "تخفیف و فرجه", "رسوبی"]
SITES = {"شعبه ولیعصر": ("ملکی", ["OP-01", "OP-02"]), "شعبه آزادی": ("استیجاری", ["OP-03", "OP-04"]),
         "شعبه ونک": ("مشارکتی", ["OP-05", "OP-06"]), "شعبه تجریش": ("پیمانکاری", ["OP-07", "OP-08"])}
OP2SITE = {o: s for s, (_, ops) in SITES.items() for o in ops}
STATUSES = ["جدید", "در حال بررسی", "تایید تخلف", "رد اتهام", "وصول و مختومه"]
WD = {5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"}
WD_ORDER = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
INSP = ["بازرس احمدی", "بازرس رستمی", "حسابرس کریمی", "بازرس نجفی"]
ROOT = ["تبانی با راننده", "سوءاستفاده نقدی", "نقص فنی سنسور/دوربین", "ضعف آموزش نرم‌افزار"]
SANC = ["تذکر کتبی", "کسر حقوق و جبران زیان", "قطع دسترسی شیفت", "ضبط سفته", "ارجاع حقوقی"]
ACT = ["تسویه نقدی", "کسر حقوق", "اصلاح سخت‌افزار", "اصلاح باگ نرم‌افزاری"]


def money(v):
    return f"{v / 1e6:,.2f} م.ت" if abs(v) >= 1e6 else f"{v:,.0f} ت"


# ------------------------------------------------------------ داده
@st.cache_data(show_spinner="در حال خواندن داده…")
def load(src):
    x = pd.ExcelFile(src)
    tx = x.parse("تراکنش_تردد")
    tx.columns = [str(c).split("\n")[-1] for c in tx.columns]
    for c in ("In_Time", "Out_Time", "Void_Time", "Shift_Date"):
        tx[c] = pd.to_datetime(tx[c], errors="coerce")
    tx["Event_Time"] = tx["Out_Time"].fillna(tx["In_Time"])
    tx["Is_Cash"], tx["Is_Void"] = tx["Pay_Mode"].eq("نقد"), tx["Void_Time"].notna()
    tx["Is_Grace"], tx["Is_Edit"] = tx["Pay_Mode"].eq("فرجه رایگان"), tx["Manual_Edit"].eq("بله")
    num = tx["Event_ID"].str[3:].astype(int)
    tx["Site"] = tx["Operator_ID"].map(OP2SITE)
    miss = tx["Site"].isna()
    tx.loc[miss, "Site"] = num[miss].map(lambda n: list(SITES)[n % 4])
    tx["Weekday"] = tx["Event_Time"].dt.weekday.map(WD)
    tx["Hour"] = tx["Event_Time"].dt.hour
    tx["NFlags"] = tx[FL].sum(axis=1)
    fd = tx["Fare_Diff"].fillna(0)
    tx["Loss"] = np.where(fd != 0, fd.abs(), np.where(tx["NFlags"] > 0, 20000, 0))
    W = pd.Series({f: v[2] for f, v in FLAGS.items()})
    prim = tx[FL].mul(W).idxmax(axis=1).where(tx["NFlags"] > 0)
    tx["Violation"], tx["Domain"] = prim.map({f: v[0] for f, v in FLAGS.items()}), prim.map({f: v[1] for f, v in FLAGS.items()})
    rc = x.parse("مغایرت_شیفت").iloc[:, :11]
    rc.columns = ["Date", "Shift", "Operator_ID", "CashPMS", "CashDeposit", "Diff", "CDR", "Alert", "CashTx", "TotalTx", "CashRatio"]
    rc["Date"] = pd.to_datetime(rc["Date"], errors="coerce")
    cap = x.parse("تراز_ظرفیت").iloc[:, :13]
    cap.columns = ["Start", "End", "Shift", "Entries", "Exits", "Expected", "Reported", "Physical", "LedgerDrift", "Ghosts", "PhysDrift", "Nominal", "Alert"]
    cap["Start"] = pd.to_datetime(cap["Start"], errors="coerce")
    nm = x.parse("اپراتورها").iloc[:, :2]
    nm.columns = ["id", "name"]
    return tx, rc.dropna(subset=["Date"]), cap.dropna(subset=["Start"]), dict(zip(nm["id"], nm["name"]))


@st.cache_data
def make_cases(tx):
    """پرونده‌ها از رویدادهای امتیاز ≥ ۳۰ ساخته می‌شوند؛ وضعیت/بازرس/اقدام شبیه‌سازی (seed ثابت) تا اتصال به سامانه پرونده."""
    c = tx[tx["Risk_Score"] >= 30].copy()
    r, n = np.random.default_rng(7), len(c)
    c["Case_ID"] = [f"CS-{i:04d}" for i in range(1, n + 1)]
    c["AI_Conf"] = (0.55 + c["Risk_Score"] / 250).clip(upper=0.98)
    c["Status"] = r.choice(STATUSES, n, p=[.2, .25, .2, .15, .2])
    c["Inspector"], c["Root"] = r.choice(INSP, n), r.choice(ROOT, n, p=[.3, .3, .25, .15])
    c["Priority"] = pd.cut(c["Loss"], [-1, 29999, 49999, 149999, 1e12], labels=["بررسی سیستمی", "متوسط", "اولویت بالا", "بحرانی"]).astype(str)
    conf = c["Status"].isin(["تایید تخلف", "وصول و مختومه"])
    closed = c["Status"].isin(["تایید تخلف", "رد اتهام", "وصول و مختومه"])
    c["Confirmed_Loss"] = np.where(conf, c["Loss"], 0)
    c["Recovered"] = np.where(c["Status"].eq("وصول و مختومه"), c["Loss"] * r.uniform(.5, 1, n), 0)
    c["Resolve_Days"] = np.where(closed, r.uniform(1, 9, n).round(1), np.nan)
    c["Sanction"] = np.where(conf, r.choice(SANC, n, p=[.3, .3, .15, .1, .15]), None)
    c["Action"] = np.where(conf, r.choice(ACT, n), None)
    return c


def sev(v, t, hi=1.5):
    return "bad" if v > t * hi else "warn" if v > t else "ok"


def kpi(col, label, value, hint, state="ok", hero=False, ac=TEAL):
    col.markdown(f'<div class="kpi {"hero" if hero else ""}" style="--ac:{ac};--sc:{STATE_C[state]}"><span class="kl">{label}</span>'
                 f'<b>{value}</b><span class="kh">{hint}</span></div>', unsafe_allow_html=True)


def banner(k, title, aud, refresh, verdict):
    st.markdown(f'<div class="ban" style="--ac:{ACC[k]}"><div><h1>{title}</h1><div class="bm"><span>مخاطب: <b>{aud}</b></span>'
                f'<span>بروزرسانی: <b>{refresh}</b></span></div></div><div class="vd"><i>در یک نگاه</i><p>{verdict}</p></div></div>',
                unsafe_allow_html=True)


def head(t, s=""):
    st.markdown(f'<div class="ct">{t}</div><div class="cs">{s}</div>', unsafe_allow_html=True)


def show(fig, h=330):
    fig.update_layout(height=h, margin=dict(l=6, r=6, t=8, b=6), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Vazirmatn, sans-serif", size=12, color=TXT), legend=dict(orientation="h", y=-0.22, title=None),
                      colorway=[TEAL, YEL, MINT, GRN, CORAL])
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)", zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def health(d):
    return 100 - d["Risk_Score"].mean() if len(d) else 100


def hstate(h):
    return "ok" if h >= 85 else "warn" if h >= 70 else "bad"


def date_scope(tx, key):
    dmin, dmax = tx["Event_Time"].min().date(), tx["Event_Time"].max().date()
    p = st.radio("بازه زمانی", ["کل بازه", "۷ روز اخیر", "دیروز", "روز آخر", "انتخاب دلخواه"], key=key)
    if p == "۷ روز اخیر": a, b = dmax - pd.Timedelta(days=6), dmax
    elif p == "دیروز": a = b = dmax - pd.Timedelta(days=1)
    elif p == "روز آخر": a = b = dmax
    elif p == "انتخاب دلخواه":
        v = st.date_input("تاریخ", (dmin, dmax), min_value=dmin, max_value=dmax, key=key + "d")
        a, b = (v if len(v) == 2 else (dmin, dmax))
    else: a, b = dmin, dmax
    return pd.Timestamp(a), pd.Timestamp(b)


def in_scope(df, col, a, b):
    return df[(df[col] >= a) & (df[col] < b + pd.Timedelta(days=1))]


# ============================================================ داشبورد ۱
def dash1(tx, cases):
    with st.sidebar:
        st.markdown("#### فیلترهای مدیریتی")
        a, b = date_scope(tx, "d1")
        sites = st.multiselect("پارکینگ / شعبه", list(SITES), default=list(SITES))
        contract = st.multiselect("مدل قراردادی", ["ملکی", "استیجاری", "مشارکتی", "پیمانکاری"], default=["ملکی", "استیجاری", "مشارکتی", "پیمانکاری"])
        risk = st.multiselect("سطح ریسک پارکینگ", ["پاک (≥85)", "نیازمند پایش (70-85)", "بحرانی (<70)"],
                              default=["پاک (≥85)", "نیازمند پایش (70-85)", "بحرانی (<70)"])
    sites = [s for s in sites if SITES[s][0] in contract]
    base = in_scope(tx, "Event_Time", a, b)
    lab = lambda h: "پاک (≥85)" if h >= 85 else "نیازمند پایش (70-85)" if h >= 70 else "بحرانی (<70)"
    sites = [s for s in sites if lab(health(base[base.Site == s])) in risk]
    d = base[base.Site.isin(sites)]
    cs = cases[cases.Event_ID.isin(d.Event_ID)]
    if d.empty:
        st.warning("با این فیلترها داده‌ای نیست."); return
    H = health(d)
    open_loss = cs.loc[cs.Status.isin(["جدید", "در حال بررسی"]), "Loss"].sum()
    conf, rec = cs["Confirmed_Loss"].sum(), cs["Recovered"].sum()
    blocked = d.loc[d.Flag_Manual_Edit_HighConf == 1, "Loss"].sum()
    arate = (d.NFlags > 0).mean()
    lb = d.groupby("Site").agg(tx=("Event_ID", "size"), anom=("NFlags", lambda s: (s > 0).mean()), loss=("Loss", "sum"), risk=("Risk_Score", "mean"))
    lb["health"] = 100 - lb["risk"]
    worst = lb["health"].idxmin()
    banner(1, "سلامت کلان شبکه و ریسک مالی", "مدیرعامل · هیئت‌مدیره · حراست کل", "روزانه / شیفتی",
           f"سلامت شبکه <b>{H:.0f} از ۱۰۰</b> است. <b>{worst}</b> با نمره <b>{lb.health.min():.0f}</b> ضعیف‌ترین شعبه است و "
           f"<b>{money(open_loss)}</b> زیان مشکوک هنوز تعیین تکلیف نشده.")
    c = st.columns([1.3, 1.3, 1, 1, 1, 1.2])
    kpi(c[0], "شاخص سلامت شبکه", f"{H:.0f}", "Score = 100 − نرخ ناهنجاری وزنی", hstate(H), True, YEL)
    kpi(c[1], "مبلغ مشکوک وصول‌نشده", money(open_loss), "پرونده‌های جدید و در حال بررسی", "bad" if open_loss else "ok", True, YEL)
    kpi(c[2], "زیان قطعی‌شده", money(conf), "پس از ممیزی", "bad" if conf else "ok")
    kpi(c[3], "پیشگیری/بازیافت", money(rec + blocked), f"بازیافت {money(rec)}")
    kpi(c[4], "نرخ تردد ناهنجار", f"{arate * 100:.1f}٪", "حداقل یک پرچم", sev(arate, .10))
    kpi(c[5], "ترافیک شبکه", f"{d.In_Time.notna().sum()} | {d.Out_Time.notna().sum()}", f"ورود | خروج · داخل: {int(d.Out_Time.isna().sum())}")
    st.write("")
    T = st.tabs(['ریسک و روند', 'حوزه\u200cها و رتبه\u200cبندی', 'ترافیک و پرداخت', 'رویدادهای پرخطر'])
    with T[0]:
        a1, a2 = st.columns(2)
        with a1.container(border=True):
            head("ماتریس ریسک پارکینگ‌ها", "X: ترددِ روزانه · Y: نرخ خطا · اندازه: مبلغ مشکوک")
            nd = max((b - a).days + 1, 1)
            m = lb.reset_index().assign(daily=lambda x: x.tx / nd)
            show(px.scatter(m, x="daily", y="anom", size="loss", color="health", text="Site", color_continuous_scale=[CORAL, YEL, GRN],
                            range_color=[60, 100], size_max=55, labels={"daily": "تردد روزانه", "anom": "نرخ خطا", "health": "سلامت"}).update_traces(textposition="top center")
                 .update_yaxes(tickformat=".0%", rangemode="tozero"), 340)
        with a2.container(border=True):
            head("روند درآمد در برابر زیان", "درآمد (محور چپ) · زیان مشکوک و قطعی (محور راست)")
            day = d.assign(day=d.Event_Time.dt.date)
            t = pd.DataFrame({"rev": day.groupby("day").Fare_Paid.sum(),
                              "susp": day[day.Risk_Score >= 30].groupby("day").Loss.sum(),
                              "conf": cs.assign(day=cs.Event_Time.dt.date).groupby("day").Confirmed_Loss.sum()}).fillna(0)
            f = go.Figure([go.Scatter(x=t.index, y=t.rev, name="درآمد", fill="tozeroy", line=dict(color=TEAL)),
                           go.Scatter(x=t.index, y=t.susp, name="زیان مشکوک", yaxis="y2", line=dict(color=YEL)),
                           go.Scatter(x=t.index, y=t.conf, name="زیان قطعی", yaxis="y2", line=dict(color=CORAL))])
            f.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False))
            show(f, 340)
    with T[1]:
        b1, b2 = st.columns([2, 3])
        with b1.container(border=True):
            head("سهم حوزه‌های تخلف از کل زیان", "تعیین اولویت سرمایه‌گذاری امنیتی")
            L = pd.Series({f: (d[f] * d.Loss / d.NFlags.replace(0, np.nan)).sum() for f in FL})
            tm = pd.DataFrame({"عنوان": [FLAGS[f][0] for f in FL], "حوزه": [FLAGS[f][1] for f in FL], "زیان": L.values}).query("زیان>0")
            show(px.treemap(tm, path=["حوزه", "عنوان"], values="زیان", color="حوزه",
                            color_discrete_sequence=[YEL, MINT, TEAL, GRN, CORAL]), 340)
        with b2.container(border=True):
            head("جدول رتبه‌بندی سلامت پارکینگ‌ها", "مقایسه عملکرد مدیران شعب")
            g = lb.reset_index().sort_values("health")
            g["وضعیت"] = g.health.map(lambda h: "🟢 عادی" if h >= 85 else "🟡 هشدار" if h >= 70 else "🔴 بحرانی")
            g["قرارداد"] = g.Site.map(lambda s: SITES[s][0])
            st.dataframe(g[["Site", "قرارداد", "health", "tx", "loss", "وضعیت"]], hide_index=True, use_container_width=True,
                         column_config={"Site": "پارکینگ", "health": st.column_config.ProgressColumn("نمره سلامت", min_value=0, max_value=100, format="%.0f"),
                                        "tx": "حجم تردد", "loss": st.column_config.NumberColumn("مبلغ زیان", format="%d")})
    with T[2]:
        x1, x2 = st.columns([3, 2])
        with x1.container(border=True):
            head("ترافیک ساعتی شبکه", "ورود و خروج در هر ساعت شبانه‌روز")
            hh = pd.DataFrame({"ورودی": d.In_Time.dt.hour.value_counts(), "خروجی": d.Out_Time.dt.hour.value_counts()}).reindex(range(24)).fillna(0)
            hh.index.name = "ساعت"
            show(px.area(hh, color_discrete_sequence=[TEAL, YEL]), 330)
        with x2.container(border=True):
            head("روش‌های پرداخت", "سهم از درآمد")
            pm = d.groupby("Pay_Mode").Fare_Paid.sum().reset_index()
            show(px.pie(pm[pm.Fare_Paid > 0], names="Pay_Mode", values="Fare_Paid", hole=.6, color_discrete_sequence=[TEAL, YEL, MINT, GRN, CORAL]), 330)
        with st.container(border=True):
            head("درآمد و زیان هر شعبه", "مقایسه مستقیم برای تصمیم بودجه بازرسی")
            sb = lb.reset_index()
            sb["درآمد"] = sb.Site.map(d.groupby("Site").Fare_Paid.sum())
            sb = sb.rename(columns={"loss": "زیان مشکوک"}).melt("Site", ["درآمد", "زیان مشکوک"])
            show(px.bar(sb, x="Site", y="value", color="variable", barmode="group", color_discrete_sequence=[TEAL, YEL]), 300)
    with T[3]:
        with st.container(border=True):
            head("رویدادهای پرخطر شبکه", "امتیاز ریسک ۳۰ یا بیشتر · مرتب بر اساس شدت")
            ev = d[d.Risk_Score >= 30].sort_values("Risk_Score", ascending=False)[["Event_ID", "Site", "Plate", "Operator_ID", "Violation", "Fare_Calc", "Fare_Paid", "Loss", "Risk_Score", "Risk_Level"]]
            st.dataframe(ev, hide_index=True, use_container_width=True, height=460,
                         column_config={"Risk_Score": st.column_config.ProgressColumn("امتیاز ریسک", min_value=0, max_value=100, format="%d")})
            st.download_button("دانلود CSV", ev.to_csv(index=False).encode("utf-8-sig"), "high_risk_events.csv", "text/csv")



# ============================================================ داشبورد ۲
def dash2(tx):
    with st.sidebar:
        st.markdown("#### فیلترهای ریشه‌یابی")
        a, b = date_scope(tx, "d2")
        dom = st.multiselect("دسته کلان", DOMAINS, default=DOMAINS)
        code = st.multiselect("کد رویداد تفصیلی", [v[0] for v in FLAGS.values()])
        gate = st.multiselect("لاین و گیت", sorted(tx.Exit_Gate.dropna().unique()))
        cal = st.radio("تقویم عملیاتی", ["همه", "روز کاری", "تعطیل (جمعه)"])
    d = in_scope(tx, "Event_Time", a, b)
    noise = int((d.ANPR_Conf_In < 0.60).sum())
    d = d[d.ANPR_Conf_In >= 0.60]  # راهنمای کالیبراسیون: نویز سخت‌افزاری وارد شاخص تقلب عمدی نمی‌شود
    if gate: d = d[d.Exit_Gate.isin(gate)]
    if cal != "همه": d = d[(d.Weekday == "جمعه") == (cal != "روز کاری")]
    fl = [f for f in FL if FLAGS[f][1] in dom and (not code or FLAGS[f][0] in code)]
    if d.empty or not fl:
        st.warning("داده‌ای برای این فیلترها نیست."); return
    ex = d[d.Out_Time.notna()]
    cnt = d[fl].sum().rename({f: FLAGS[f][0] for f in fl}).sort_values(ascending=False)
    cnt = cnt[cnt > 0]
    cum = cnt.cumsum() / cnt.sum()
    n80 = int((cum < 0.8).sum() + 1)
    moe = (ex.Is_Edit & (ex.ANPR_Conf_In >= .85)).mean()
    ov = ex.Barrier_Dwell[ex.Barrier_Dwell > 8] - 8
    banner(2, "ریشه‌یابی و طبقه‌بندی الگوهای خطا", "تیم علم داده · مهندسین BI · تضمین کیفیت داده", "ساعتی / روزانه",
           f"از <b>{int(cnt.sum())}</b> رخداد غیرعادی، فقط <b>{n80} علت</b> ({cnt.index[0]} در صدر) <b>۸۰٪</b> خطاها را می‌سازند؛ "
           f"قوانین Rule Engine را اول روی همین‌ها اصلاح کنید. <b>{noise}</b> رویداد با اطمینان OCR زیر ۰.۶۰ به‌عنوان نویز کنار گذاشته شد.")
    c = st.columns([1.4, 1.4, 1, 1, 1, 1])
    kpi(c[0], "کل رخدادهای غیرعادی", f"{int(cnt.sum())}", "شمارش پرچم‌های سیستمی، سخت‌افزاری و مالی", "warn", True, MINT)
    kpi(c[1], "علل پوشش‌دهنده ۸۰٪ خطا", f"{n80} از {len(cnt)}", "قاعده پارتو ۸۰/۲۰", "ok", True, MINT)
    kpi(c[2], "ویرایش دستی پلاک (MOE)", f"{moe * 100:.1f}٪", "اطمینان OCR بالای ۰.۸۵", sev(moe, .035))
    kpi(c[3], "ترخیص در فرجه", f"{ex.Is_Grace.mean() * 100:.1f}٪", "آستانه ۵٪", sev(ex.Is_Grace.mean(), .05))
    kpi(c[4], "ابطال پس از خروج", f"{ex.Is_Void.mean() * 100:.1f}٪", "آستانه ۲٪", sev(ex.Is_Void.mean(), .02))
    kpi(c[5], "عبور چندگانه", f"{int(d.Flag_Tailgating.sum())}", f"مازاد راهبند {ov.mean() if len(ov) else 0:.1f} ث", "bad" if d.Flag_Tailgating.sum() else "ok")
    st.write("")
    T = st.tabs(['پارتو و زمان', 'گیت و جریان', 'کیفیت OCR و نویز', 'فهرست رخدادها'])
    with T[0]:
        p1, p2 = st.columns(2)
        with p1.container(border=True):
            head("نمودار پارتو علل خطا", "فراوانی نزولی + منحنی تجمعی (خط ۸۰٪)")
            f = go.Figure([go.Bar(x=cnt.index, y=cnt.values, name="فراوانی", marker_color=MINT),
                           go.Scatter(x=cnt.index, y=cum.values, name="تجمعی", yaxis="y2", line=dict(color=YEL), mode="lines+markers")])
            f.add_hline(y=.8, line_dash="dash", line_color=CORAL, yref="y2")
            f.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 1.02], tickformat=".0%", showgrid=False))
            show(f, 380)
        with p2.container(border=True):
            head("نقشه حرارتی زمانی تخلف", "ساعت (۲۴) × روز هفته")
            hm = d.assign(n=d[fl].sum(axis=1)).pivot_table(index="Weekday", columns="Hour", values="n", aggfunc="sum").reindex(index=WD_ORDER, columns=range(24)).fillna(0)
            show(px.imshow(hm, aspect="auto", color_continuous_scale=[DEEP, TEAL, YEL], labels=dict(x="ساعت", y="", color="رخداد")), 380)
    with T[1]:
        q1, q2 = st.columns([2, 3])
        with q1.container(border=True):
            head("توزیع دسته‌های خطا به تفکیک گیت", "کشف گیت‌ها و لاین‌های معیوب یا مستعد تبانی")
            rows = [{"گیت": g, "دسته": dm, "تعداد": int(sub[[f for f in fl if FLAGS[f][1] == dm]].sum().sum())}
                    for g, sub in d.groupby("Exit_Gate") for dm in DOMAINS if any(FLAGS[f][1] == dm for f in fl)]
            show(px.bar(pd.DataFrame(rows), x="گیت", y="تعداد", color="دسته", color_discrete_sequence=[YEL, MINT, TEAL, GRN, CORAL]), 360)
        with q2.container(border=True):
            head("جریان تخلفات", "دسته خطا ← پارکینگ ← شیفت ← صندوقدار")
            s = d[(d.NFlags > 0) & d.Operator_ID.notna()].assign(Shift2="شیفت " + d.Shift.astype(str))
            s = s[s.Domain.isin(dom)]
            if s.empty: st.info("جریانی برای نمایش نیست.")
            else:
                pairs = pd.concat([s.groupby(["Domain", "Site"]).size().reset_index().set_axis(["a", "b", "v"], axis=1),
                                   s.groupby(["Site", "Shift2"]).size().reset_index().set_axis(["a", "b", "v"], axis=1),
                                   s.groupby(["Shift2", "Operator_ID"]).size().reset_index().set_axis(["a", "b", "v"], axis=1)])
                nodes = list(pd.unique(pairs[["a", "b"]].values.ravel()))
                ix = {n: i for i, n in enumerate(nodes)}
                f = go.Figure(go.Sankey(node=dict(label=nodes, color=TEAL, pad=14, thickness=14),
                                        link=dict(source=pairs.a.map(ix), target=pairs.b.map(ix), value=pairs.v, color="rgba(136,207,192,.35)")))
                show(f, 360)
    with T[2]:
        o1, o2 = st.columns(2)
        with o1.container(border=True):
            head("اطمینان پلاک‌خوان و ویرایش دستی", "خط نقطه‌چین = مرز نویز ۰.۶۰ · خط ممتد = آستانه تقلب ۰.۸۵")
            g = px.histogram(tx[tx.Out_Time.notna()], x="ANPR_Conf_In", color="Manual_Edit", nbins=40, barmode="overlay",
                             color_discrete_map={"بله": CORAL, "خیر": MINT})
            g.add_vline(x=.6, line_dash="dot", line_color=YEL)
            g.add_vline(x=.85, line_color=TXT)
            show(g, 340)
        with o2.container(border=True):
            head("مدت باز ماندن راهبند", "خط قرمز = آستانه ۱۲ ثانیه")
            g = px.histogram(ex, x="Barrier_Dwell", nbins=40, color_discrete_sequence=[TEAL])
            g.add_vline(x=12, line_dash="dash", line_color=CORAL)
            show(g, 340)
        st.markdown(f'<div class="note">{noise} رویداد با اطمینان OCR زیر ۰.۶۰ نویز سخت‌افزاری تلقی و از شاخص تقلب عمدی حذف شد.</div>', unsafe_allow_html=True)
    with T[3]:
        with st.container(border=True):
            head("فهرست رخدادهای غیرعادی", "فقط پرچم‌های انتخاب‌شده در فیلتر")
            cols = ["Event_ID", "Site", "Plate", "Exit_Gate", "Operator_ID", "Out_Time", "Risk_Score"] + fl
            lst = d[d[fl].sum(axis=1) > 0].sort_values("Risk_Score", ascending=False)[cols].rename(columns={f: FLAGS[f][0] for f in fl})
            st.dataframe(lst, hide_index=True, use_container_width=True, height=460)
            st.download_button("دانلود CSV", lst.to_csv(index=False).encode("utf-8-sig"), "anomaly_events.csv", "text/csv")



# ============================================================ داشبورد ۳
def z(s):
    return (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) else s * 0


def dash3(tx, rc, cap, names):
    with st.sidebar:
        st.markdown("#### فیلترهای عملیاتی")
        site = st.selectbox("پارکینگ", list(SITES))
        shift = st.multiselect("شیفت کاری", ["صبح", "عصر", "شب"])
        ops = st.multiselect("صندوقدار", SITES[site][1], format_func=lambda o: f"{o} · {names.get(o, '')}")
        tar = st.multiselect("نوع تعرفه", sorted(tx.Tariff_Type.dropna().unique()))
    full = tx[tx.Site == site]
    d = full.copy()
    if shift: d = d[d.Shift.isin(shift)]
    if ops: d = d[d.Operator_ID.isin(ops)]
    if tar: d = d[d.Tariff_Type.isin(tar)]
    if d.empty:
        st.warning("داده‌ای برای این فیلترها نیست."); return
    r = rc[rc.Operator_ID.isin(SITES[site][1])]
    if shift: r = r[r.Shift.isin(shift)]
    if ops: r = r[r.Operator_ID.isin(ops)]
    short = (r.CashPMS - r.CashDeposit).sum()
    H = health(d)
    inlot = d[d.Out_Time.isna()]
    ghosts = inlot[(inlot.Duration > 2880) & (inlot.Slot_Sensor_Status == "خالی")]
    cash = d.loc[d.Is_Cash, "Fare_Paid"].sum() / max(d.Fare_Paid.sum(), 1)
    manual = int((d.Manual_Barrier_Open == "بله").sum())
    # پروتکل واکنش میدانی: Z نقد و ابطال > 2.5
    allops = tx[tx.Operator_ID.notna()].groupby("Operator_ID").agg(cash=("Is_Cash", "mean"), void=("Is_Void", "mean"))
    zz = pd.DataFrame({"cash": z(allops.cash), "void": z(allops["void"])})
    hit = zz[(zz.cash > 2.5) & (zz["void"] > 2.5)].index.tolist()
    top = (zz.cash + zz["void"]).idxmax()
    banner(3, f"پایش میدانی {site}", "مدیر پارکینگ · سرپرست شیفت · بازرس مقیم", "لحظه‌ای (< ۵ دقیقه)",
           f"کسری دخل شیفت‌ها <b>{money(short)}</b>؛ <b>{len(ghosts)}</b> خودرو رسوبی مشکوک داخل پارکینگ است و راهبند <b>{manual}</b> بار دستی باز شده. "
           f"{'<b>بازرسی سرزده برای ' + '، '.join(hit) + ' لازم است.</b>' if hit else 'اپراتوری از آستانه بازرسی سرزده عبور نکرده.'}")
    if hit:
        st.markdown(f'<div class="alert bad">پروتکل واکنش میدانی: Z-Score نقد و ابطال {"، ".join(hit)} از ۲.۵ گذشت · پیامک بازرسی سرزده برای مدیر شیفت ارسال می‌شود.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert ok">پروتکل واکنش میدانی: پایین‌تر از آستانه ۲.۵؛ بالاترین ریسک {top} ({names.get(top, "")}) با Z نقد {zz.cash[top]:.2f} و Z ابطال {zz["void"][top]:.2f}</div>', unsafe_allow_html=True)
    c = st.columns([1.4, 1.4, 1, 1, 1, 1])
    kpi(c[0], "کسری و مغایرت دخل شیفت", money(short), "نقد PMS − مبلغ تحویلی", "bad" if short > 0 else "ok", True, TEAL)
    kpi(c[1], "خودروهای رسوبی پرریسک", f"{len(ghosts)}", f"از {len(inlot)} خودرو داخل · توقف > ۴۸ ساعت", "bad" if len(ghosts) else "ok", True, TEAL)
    kpi(c[2], "سلامت پارکینگ", f"{H:.0f}", "۰ تا ۱۰۰", hstate(H))
    kpi(c[3], "انحراف تراز ظرفیت", f"{int(cap.LedgerDrift.max())}", "حداکثر |فیزیکی − سیستم|", "bad" if cap.LedgerDrift.max() > 2 else "ok")
    kpi(c[4], "نسبت نقد", f"{cash * 100:.0f}٪", "سهم نقد از درآمد", "warn" if cash > .4 else "ok")
    kpi(c[5], "بازگشایی دستی راهبند", f"{manual}", "کلید سخت‌افزاری", "bad" if manual else "ok")
    st.write("")
    T = st.tabs(['صندوقداران و جریان زنده', 'تجهیزات گیت', 'خودروهای رسوبی', 'مغایرت دخل و ظرفیت'])
    with T[0]:
        p = d[d.Operator_ID.notna()].groupby("Operator_ID").agg(cash=("Is_Cash", "mean"), void=("Is_Void", "mean"), edit=("Is_Edit", "mean"), grace=("Is_Grace", "mean"))
        p = p.reindex(SITES[site][1]).dropna()
        r1, r2 = st.columns(2)
        with r1.container(border=True):
            head("رادار ریسک صندوقدار", "هر محور نسبت به بیشترین مقدار همکاران")
            sel = st.selectbox("صندوقدار", list(p.index), format_func=lambda o: f"{o} · {names.get(o, '')}", label_visibility="collapsed")
            nm = p / p.max().replace(0, 1)
            cats = ["نقد", "ابطال", "ویرایش پلاک", "فرجه"]
            f = go.Figure([go.Scatterpolar(r=list(nm.loc[sel]) + [nm.loc[sel].iloc[0]], theta=cats + cats[:1], fill="toself", name=sel, line_color=CORAL),
                           go.Scatterpolar(r=list(nm.mean()) + [nm.mean().iloc[0]], theta=cats + cats[:1], fill="toself", name="میانگین همکاران", line_color=MINT)])
            f.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,.15)")))
            show(f, 340)
        with r2.container(border=True):
            head("جریان زنده تردد", "پالس لوپ در برابر فیش صادرشده هر ۱۰ دقیقه · ۶ ساعت آخر")
            e = d[d.Out_Time.notna()]
            e = e[e.Out_Time >= e.Out_Time.max() - pd.Timedelta(hours=6)]
            s = e.groupby(e.Out_Time.dt.floor("10min")).agg(pulses=("Loop_Pulses", "sum"), tickets=("Recorded_Transactions", "sum")).reset_index()
            bad = s[s.pulses > s.tickets]
            f = go.Figure([go.Scatter(x=s.Out_Time, y=s.tickets, name="فیش صادرشده", fill="tozeroy", line_color=TEAL),
                           go.Scatter(x=s.Out_Time, y=s.pulses, name="پالس لوپ", line_color=YEL),
                           go.Scatter(x=bad.Out_Time, y=bad.pulses, name="مغایرت", mode="markers", marker=dict(color=CORAL, size=11))])
            show(f, 340)
    with T[1]:
        st.markdown("##### وضعیت تلمتری تجهیزات گیت‌ها")
        gc = st.columns(4)
        for col, g in zip(gc, ["E1", "E2", "X1", "X2"]):
            s = full[full.Exit_Gate == g]
            chips = [("دوربین OCR", s.Camera_Drop_Sec.max() < 120 if len(s) else True), ("لوپ زمین", (s.Flag_Tailgating.sum() == 0) if len(s) else True),
                     ("رله راهبند", (s.Flag_Barrier_Keep_Open.sum() == 0) if len(s) else True), ("ساعت NTP", (s.Server_Time_Diff.abs().max() < 30) if len(s) else True)]
            col.markdown(f'<div class="eq"><h4>گیت {g}</h4>' + "".join(f'<span class="chip {"ok" if v else "bad"}">{k} {"✓" if v else "✕"}</span>' for k, v in chips) + "</div>", unsafe_allow_html=True)
        st.write("")
    with T[2]:
        with st.container(border=True):
            head("کارتابل خودروهای رسوبی بحرانی", "تا ورود به تصویر ورود، پلاک و مدت توقف را به نگهبان شیفت بدهید")
            swap = set(tx.loc[tx.Flag_Ticket_Swap == 1, "Plate"])
            g = inlot.copy()
            g["days"] = (g.Duration / 1440).round(1)
            g["cost"] = (g.Duration // 1440) * 180000 + 20000
            g["alert"] = np.where(g.Plate.isin(swap), "⚠ احتمال تعویض فیش", np.where(g.Slot_Sensor_Status == "خالی", "سنسور خالی", "عادی"))
            st.dataframe(g.sort_values("days", ascending=False)[["Plate", "Vehicle_Model", "In_Time", "days", "cost", "Slot_Sensor_Status", "alert"]],
                         hide_index=True, use_container_width=True, height=300,
                         column_config={"Plate": "پلاک", "Vehicle_Model": "مدل", "In_Time": "زمان ورود", "days": "توقف (روز)",
                                        "cost": st.column_config.NumberColumn("هزینه تجمیعی (ت)", format="%d"), "Slot_Sensor_Status": "سنسور جای پارک", "alert": "هشدار"})
    with T[3]:
        y1, y2 = st.columns(2)
        with y1.container(border=True):
            head("نرخ کسری نقد هر شیفت", "خط زرد = آستانه ۱.۵٪")
            rr = r.assign(lbl=r.Date.dt.strftime("%m-%d") + " " + r.Shift + " " + r.Operator_ID)
            fg = px.bar(rr, x="lbl", y="CDR", color="Alert", color_discrete_map={"قرمز": CORAL, "عادی": TEAL})
            fg.add_hline(y=.015, line_dash="dash", line_color=YEL)
            fg.update_yaxes(tickformat=".0%")
            show(fg, 330)
        with y2.container(border=True):
            head("اشغال پارکینگ", "دفتری، گزارش سیستم و سنسور فیزیکی")
            lg = cap.melt("Start", ["Expected", "Reported", "Physical"], var_name="نوع", value_name="خودرو")
            lg["نوع"] = lg["نوع"].map({"Expected": "مورد انتظار", "Reported": "گزارش سیستم", "Physical": "سنسور فیزیکی"})
            show(px.line(lg, x="Start", y="خودرو", color="نوع"), 330)
        with st.container(border=True):
            head("شیفت‌های دارای مغایرت")
            st.dataframe(r[r.CDR > 0][["Date", "Shift", "Operator_ID", "CashPMS", "CashDeposit", "Diff", "CDR"]].sort_values("CDR", ascending=False),
                         hide_index=True, use_container_width=True)



# ============================================================ داشبورد ۴
def dash4(cases):
    ov = st.session_state.setdefault("ov", {})
    cs = cases.copy()
    cs["Status"] = cs.Case_ID.map(ov).fillna(cs.Status)
    with st.sidebar:
        st.markdown("#### فیلترهای پرونده")
        stt = st.multiselect("وضعیت پرونده", STATUSES, default=STATUSES)
        pri = st.multiselect("سطح اولویت", ["بحرانی", "اولویت بالا", "متوسط", "بررسی سیستمی"], default=["بحرانی", "اولویت بالا", "متوسط", "بررسی سیستمی"])
        ins = st.multiselect("کارشناس پیگیری‌کننده", INSP)
        act = st.multiselect("نوع اقدام نهایی", ACT)
    f = cs[cs.Status.isin(stt) & cs.Priority.isin(pri)]
    if ins: f = f[f.Inspector.isin(ins)]
    if act: f = f[f.Action.isin(act)]
    if f.empty:
        st.warning("پرونده‌ای با این فیلترها نیست."); return
    n = len(f)
    pend = f.Status.isin(["جدید", "در حال بررسی"])
    confirmed = f[f.Status.isin(["تایید تخلف", "وصول و مختومه"])]
    fp = (f.Status == "رد اتهام").mean()
    mttr = f.Resolve_Days.mean()
    cl = confirmed.Confirmed_Loss.sum()
    recp = f.Recovered.sum() / cl if cl else 0
    off = confirmed.groupby("Operator_ID").size()
    rep = (off > 1).mean() if len(off) else 0
    crit = f[pend & (f.Priority == "بحرانی")]
    banner(4, "مدیریت پرونده‌ها و مختومه‌سازی", "کمیته انضباطی · حسابرسی داخلی · حراست و حقوقی", "رویدادمحور",
           f"<b>{int(pend.sum())} پرونده</b> منتظر تصمیم شماست که <b>{len(crit)}</b> تای آن بحرانی است. تا امروز <b>{len(confirmed)}</b> تخلف اثبات و "
           f"<b>{recp * 100:.0f}٪</b> زیان آن وصول شده؛ هر پرونده به‌طور میانگین <b>{mttr:.1f} روز</b> طول می‌کشد.")
    st.markdown('<div class="note">وضعیت، بازرس و اقدام نهایی پرونده‌ها شبیه‌سازی (seed ثابت) است؛ با اتصال به سامانه پرونده، ستون‌های Status/Inspector/Action را جایگزین کنید.</div>', unsafe_allow_html=True)
    c = st.columns([1.4, 1.4, 1, 1, 1, 1])
    kpi(c[0], "پرونده‌های در دست ممیزی", f"{int(pend.sum())}", f"از {n} پرونده · جدید + در حال بررسی", "warn" if pend.sum() else "ok", True, GRN)
    kpi(c[1], "تخلفات قطعی اثبات‌شده", f"{len(confirmed)}", f"زیان قطعی {money(cl)}", "bad" if len(confirmed) else "ok", True, GRN)
    kpi(c[2], "نرخ مثبت کاذب", f"{fp * 100:.0f}٪", "هشدار رد‌شده / کل", sev(fp, .2))
    kpi(c[3], "میانگین زمان رسیدگی", f"{mttr:.1f} روز", "MTTR", sev(mttr, 5))
    kpi(c[4], "درصد وصول خسارت", f"{recp * 100:.0f}٪", "وصول‌شده / زیان قطعی", "ok" if recp > .6 else "warn")
    kpi(c[5], "تکرار تخلف پرسنل", f"{rep * 100:.0f}٪", "اپراتور با بیش از یک پرونده قطعی", "bad" if rep else "ok")
    st.write("")
    T = st.tabs(['گردش\u200cکار پرونده\u200cها', 'علل، احکام و ثبت وضعیت', 'عملکرد و مالی'])
    with T[0]:
        k1, k2 = st.columns([2, 3])
        with k1.container(border=True):
            head("قیف چرخه عمر پرونده‌ها", "گلوگاه‌های اداری")
            cnt = f.Status.value_counts()
            fin = cnt.get("تایید تخلف", 0) + cnt.get("رد اتهام", 0) + cnt.get("وصول و مختومه", 0)
            st_ = [("کشف هوشمند", n), ("تخصیص بازرس", n - cnt.get("جدید", 0)), ("بازجویی اپراتور", fin + round(cnt.get("در حال بررسی", 0) / 2)),
                   ("اثبات / تبرئه", fin), ("وصول خسارت", cnt.get("وصول و مختومه", 0))]
            show(go.Figure(go.Funnel(y=[a for a, _ in st_], x=[v for _, v in st_], marker=dict(color=[YEL, MINT, TEAL, GRN, "#6F8C90"]))), 340)
        with k2.container(border=True):
            head("کارتابل رویدادهای بازرسی", "برای تغییر وضعیت، شناسه پرونده را در پایین انتخاب کنید")
            st.dataframe(f.sort_values("Risk_Score", ascending=False)[["Case_ID", "Priority", "Site", "Operator_ID", "Violation", "AI_Conf", "Loss", "Inspector", "Status"]],
                         hide_index=True, use_container_width=True, height=340,
                         column_config={"Case_ID": "پرونده", "Priority": "اولویت", "Site": "پارکینگ", "Operator_ID": "اپراتور", "Violation": "عنوان تخلف",
                                        "AI_Conf": st.column_config.ProgressColumn("اطمینان AI", min_value=0, max_value=1, format="%.2f"),
                                        "Loss": st.column_config.NumberColumn("زیان (ت)", format="%d"), "Inspector": "کارشناس", "Status": "وضعیت"})
    with T[1]:
        d1, d2, d3 = st.columns(3)
        with d1.container(border=True):
            head("علل ریشه‌ای تخلفات")
            r = f.Root.value_counts().sort_values().reset_index()
            show(px.bar(r, x="count", y="Root", orientation="h", color_discrete_sequence=[MINT]).update_layout(xaxis_title="", yaxis_title=""), 300)
        with d2.container(border=True):
            head("توزیع احکام انضباطی")
            sn = confirmed.Sanction.value_counts().reset_index()
            show(px.pie(sn, names="Sanction", values="count", hole=.55, color_discrete_sequence=[YEL, MINT, TEAL, GRN, CORAL]), 300)
        with d3.container(border=True):
            head("بررسی و ثبت وضعیت")
            cid = st.selectbox("شناسه پرونده", f.Case_ID.tolist(), label_visibility="collapsed")
            row = f[f.Case_ID == cid].iloc[0]
            st.caption(f"{row.Violation} · پلاک {row.Plate} · {row.Site}\n\nخروج: {row.Out_Time} · RRN: {row.POS_RRN if pd.notna(row.POS_RRN) else '—'} · فیش {row.Ticket_No}")
            new = st.selectbox("وضعیت جدید", STATUSES, index=STATUSES.index(row.Status))
            if st.button("ثبت وضعیت", use_container_width=True):
                ov[cid] = new
                st.rerun()
    with T[2]:
        z1, z2 = st.columns(2)
        with z1.container(border=True):
            head("زیان قطعی و وصول به تفکیک شعبه")
            v = f.groupby("Site").agg(قطعی=("Confirmed_Loss", "sum"), وصول=("Recovered", "sum")).reset_index().melt("Site")
            show(px.bar(v, x="Site", y="value", color="variable", barmode="group", color_discrete_sequence=[CORAL, TEAL]), 320)
        with z2.container(border=True):
            head("میانگین زمان رسیدگی هر کارشناس (روز)")
            m = f.groupby("Inspector").Resolve_Days.mean().reset_index()
            show(px.bar(m, x="Inspector", y="Resolve_Days", color_discrete_sequence=[MINT]), 320)
        with st.container(border=True):
            head("اپراتورهای دارای بیشترین پرونده", "برای شناسایی تکرار تخلف")
            o = f.groupby("Operator_ID").agg(پرونده=("Case_ID", "size"), زیان=("Loss", "sum"),
                                              تایید_شده=("Status", lambda s: s.isin(["تایید تخلف", "وصول و مختومه"]).sum())).reset_index()
            st.dataframe(o.sort_values("پرونده", ascending=False), hide_index=True, use_container_width=True)



# ============================================================ اجرا
default = HERE / "parking_fraud_dataset.xlsx"
with st.sidebar:
    if (HERE / "logo.jpg").exists(): st.image(str(HERE / "logo.jpg"), use_container_width=True)
    up = st.file_uploader("فایل داده (اختیاری)", type=["xlsx"])
    src = up or (default if default.exists() else None)
    if src is None:
        st.error("فایل parking_fraud_dataset.xlsx کنار app.py نیست؛ آپلود کنید."); st.stop()
    page = st.radio("داشبورد", ["۱ · سلامت کلان · مدیرعامل", "۲ · ریشه‌یابی خطا · علم داده", "۳ · پایش پارکینگ · مدیر پارکینگ", "۴ · پرونده‌ها · کمیته انضباطی"])
    st.divider()
tx, rc, cap, names = load(src)
cases = make_cases(tx)
st.sidebar.caption("داده نمونه تک‌پارکینگ است؛ برای نمایش ساختار چندشعبه‌ای، اپراتورها بین ۴ شعبه فرضی تقسیم شده‌اند.")
key = page[0].translate(str.maketrans("۱۲۳۴", "1234"))
{"1": lambda: dash1(tx, cases), "2": lambda: dash2(tx), "3": lambda: dash3(tx, rc, cap, names), "4": lambda: dash4(cases)}[key]()
