import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------- palette (same as the Audience page) ----------
MAROON, GOLD = "#5E1A10", "#CCBA8C"
PANEL, BORDER, TEXT, MUTED = "#F8F5EE", "#D9D2C2", "#2B2B2B", "#6B6358"
PAGE = "#E9E5DB"
TIER_COLORS = {"High": MAROON, "Mid": GOLD, "Small": "#A8A196"}

st.markdown(f"""
<style>
.block-container {{padding-top:0.6rem; padding-bottom:0.6rem; max-width:1500px;}}
div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"] {{gap:12px !important;}}
header[data-testid="stHeader"] {{background:transparent;}}
.band {{background:{MAROON}; color:#F8F5EE; padding:10px 20px; border-radius:8px; margin:0;}}
.band h1 {{color:#F8F5EE; font-size:1.35rem; margin:0; padding:0; line-height:1.3;}}
.band p {{color:{GOLD}; margin:0; font-size:.8rem;}}
.card {{background:{PANEL}; border:1px solid {BORDER}; border-radius:8px; padding:0 0 6px 0;
        box-shadow:2px 2px 4px rgba(0,0,0,.08); text-align:center; overflow:hidden;}}
.card .t {{background:{BORDER}; color:{TEXT}; font-size:.68rem; font-weight:600; padding:3px;}}
.card .v {{font-size:1.4rem; font-weight:600; color:{TEXT}; padding-top:2px; line-height:1.2;}}
.card .s {{font-size:.64rem; color:{MUTED};}}
.box {{background:{PANEL}; border:1px solid {BORDER}; border-radius:8px; padding:10px 16px;
       box-sizing:border-box; height:340px; overflow:hidden;}}
.box, .box h4, .box li, .box p {{color:{TEXT} !important;}}
.box h4 {{margin:0 0 4px 0; font-size:.95rem;}}
.box li {{margin-bottom:4px; font-size:.85rem;}}
.box p {{font-size:.8rem; color:{MUTED} !important; margin:6px 0 0 0;}}
.foot {{color:{MUTED}; font-size:.72rem; margin:0;}}
.tblbox {{padding:8px 12px;}}
.ptbl {{width:100%; border-collapse:collapse; font-size:.7rem; color:{TEXT};}}
.ptbl th {{text-align:left; border-bottom:1px solid {BORDER}; padding:1px 6px; font-weight:600;}}
.ptbl td {{padding:1px 6px; border-bottom:1px solid {BORDER}; line-height:1.2; white-space:nowrap;}}
div[data-testid="stPlotlyChart"] {{background:{PANEL}; border:1px solid {BORDER}; border-radius:8px; padding:0; overflow:hidden;}}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    p = pd.read_csv("data/partners.csv")
    m = pd.read_csv("data/sponsors_master.csv")
    m["industry"] = (m["industry"].str.replace("_and_", " & ").str.replace("_", " ").str.title())
    s = pd.read_csv("data/survey_clean.csv", dtype={"zip": str})
    s["region"] = s["region"].fillna("Unknown")
    return p, m, s

partners, master, survey = load()

# ---------- numbers ----------
METRO = ["Denver", "South / southeast suburbs", "West suburbs", "North suburbs"]
inc = survey["Income Order"].dropna()
reg = survey[survey["region"] != "Unknown"]
hi_share = (inc >= 5).mean()
metro_share = reg["region"].isin(METRO).mean()

n_master = len(master)
n_industries = master["industry"].nunique()
recent = (partners["Year"] >= 2024).sum()
n_high = (partners["Tier"] == "High").sum()
master_names = set(master["partner"].str.strip().str.lower())
missing = [n for n in partners["Partner"].str.strip().str.lower() if n not in master_names]
missing_names = partners.loc[partners["Partner"].str.lower().isin(missing), "Partner"].tolist()

# ---------- header ----------
# page buttons (replace the sidebar menu)
n1, n2, _ = st.columns([1.3, 1, 8])
n1.page_link("audience.py", label="Audience Profile")
n2.page_link("partners.py", label="Partners")

st.markdown('<div style="padding-bottom:10px"><div class="band"><h1>DU Hockey Partner Portfolio</h1>'
            '<p>Who partners with DU Hockey today</p></div></div>',
            unsafe_allow_html=True)

cards = [("Partners on Master List", f"{n_master}", f"{n_industries} industries"),
         ("Partners with Tier Data", f"{len(partners)}", f"{n_high} High, "
          f"{(partners['Tier'] == 'Mid').sum()} Mid, {(partners['Tier'] == 'Small').sum()} Small"),
         ("Started in 2024-25", f"{recent / len(partners):.0%}", f"{recent} of {len(partners)} tiered partners"),
         ("High-Tier Partners", f"{n_high / len(partners):.0%}", f"{n_high} of {len(partners)} tiered partners")]
for col, (t, v, s) in zip(st.columns(4), cards):
    col.markdown(f'<div style="padding-bottom:16px"><div class="card"><div class="t">{t}</div>'
                 f'<div class="v">{v}</div><div class="s">{s}</div></div></div>', unsafe_allow_html=True)


def style(fig, h, title):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=44, b=10), paper_bgcolor=PANEL,
                      plot_bgcolor=PANEL, font=dict(color=TEXT),
                      title=dict(text=title, x=0.02, font=dict(size=13)), showlegend=False)
    return fig

# ---------- row 2: industry mix, start year, partner table ----------
c1, c2, c3 = st.columns([1.05, 0.9, 1.55])

ind = master["industry"].value_counts().sort_values()
ifig = go.Figure(go.Bar(x=ind.values, y=ind.index, orientation="h", marker_color=MAROON,
                        text=ind.values, textposition="outside"))
ifig.update_xaxes(visible=False, range=[0, ind.max() * 1.2])
ifig.update_yaxes(tickfont=dict(size=10))
c1.plotly_chart(style(ifig, 340, "Partners by Industry"), width="stretch")

by_year = partners.groupby(["Year", "Tier"]).size().reset_index(name="n")
yfig = go.Figure()
for tier in ["High", "Mid", "Small"]:
    d = by_year[by_year["Tier"] == tier]
    yfig.add_bar(x=d["Year"].astype(str), y=d["n"], name=tier, marker_color=TIER_COLORS[tier])
yfig.update_layout(barmode="stack", showlegend=True, legend=dict(orientation="h", y=1.0, x=1, xanchor="right"))
yfig.update_xaxes(type="category", categoryorder="array",
                  categoryarray=[str(y) for y in sorted(partners["Year"].unique())])
yfig.update_yaxes(dtick=1, gridcolor=BORDER)
fy = style(yfig, 340, "Partners by Start Year and Tier")
fy.update_layout(showlegend=True)
c2.plotly_chart(fy, width="stretch")

tbl = partners.copy()
tbl["Tier"] = pd.Categorical(tbl["Tier"], ["High", "Mid", "Small"], ordered=True)
tbl = tbl.sort_values(["Tier", "Year"]).rename(columns={"Year": "Started"})
tbl["Started"] = tbl["Started"].astype(str)
rows = "".join(
    f"<tr><td>{html.escape(r.Partner)}</td><td>{html.escape(r.Category)}</td>"
    f"<td><span style='color:{TIER_COLORS[r.Tier]}'>&#9679;</span> {r.Tier}</td>"
    f"<td>{r.Exclusive}</td><td>{r.Started}</td></tr>" for r in tbl.itertuples())
c3.markdown(f'<div class="box tblbox"><h4>All Tiered Partners</h4><table class="ptbl"><thead><tr>'
            f'<th>Partner</th><th>Category</th><th>Tier</th><th>Exclusive</th><th>Started</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

# ---------- row 3: ideas + caveats ----------
c4, c5 = st.columns(2)
present = " ".join(master["industry"].str.lower()) + " " + " ".join(partners["Category"].str.lower())
oos = (reg["region"] == "Out of state").mean()
# (idea, keywords that would mean the category is already covered, supporting audience fact)
ideas = [("Real Estate / Mortgage", ["real estate", "mortgage"], f"{metro_share:.0%} of respondents live in the Denver metro and {hi_share:.0%} of those who answered earn $100K+"),
         ("Telecom / Wireless", ["telecom", "wireless"], f"{metro_share:.0%} of respondents live in the Denver metro, a local household audience"),
         ("Energy / Utilities", ["energy", "utilit", "electric"], f"{metro_share:.0%} of respondents live in the Denver metro"),
         ("Travel / Airlines", ["travel", "airline"], f"{oos:.0%} of respondents live outside Colorado")]
ideas = [(n, w) for n, k, w in ideas if not any(x in present for x in k)]
li = "".join(f"<li><b>{n}</b>: {w}.</li>" for n, w in ideas)
c4.markdown(f'<div class="box"><h4>Ideas to Test: Categories to Consider</h4><ul>{li}</ul></div>',
            unsafe_allow_html=True)

caveats = [f"The tiered list ({len(partners)}) and the master list ({n_master}) do not match. "
           f"{len(missing_names)} tiered partners are not on the master list: {', '.join(missing_names)}.",
           "No dollar amounts are available, so tiers (High, Mid, Small) are labels only.",
           "Exclusive is only filled in for 9 of 14 partners. What a blank means, and what "
           "category an exclusive covers, is not confirmed.",
           "There are no lapsed partners in either list, so renewal patterns cannot be measured. "
           "Only 5 partners are marked as renewed."]
li = "".join(f"<li>{c}</li>" for c in caveats)
c5.markdown(f'<div class="box"><h4>What This Data Can and Cannot Tell Us</h4><ul>{li}</ul></div>',
            unsafe_allow_html=True)

st.markdown(f'<div style="padding-top:16px"><div class="foot">Source: DU Athletics sponsor lists. '
            f'Audience figures use the fan survey ({len(survey):,} respondents).</div></div>',
            unsafe_allow_html=True)
