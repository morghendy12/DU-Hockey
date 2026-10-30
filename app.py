import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="DU Hockey Audience Profile", layout="wide")

# ---------- palette ----------
MAROON, GOLD = "#5E1A10", "#CCBA8C"
PANEL, BORDER, TEXT, MUTED = "#F8F5EE", "#D9D2C2", "#2B2B2B", "#6B6358"
RAMP = [MAROON, GOLD, "#6B6358", "#A8A196", "#8E3426", "#B25A47", "#E3B4A9"]

INCOME_ORDER = ["Less than $25,000", "$25,000-$49,999", "$50,000-$74,999",
                "$75,000-$99,999", "$100,000-$149,999", "$150,000 or more"]
METRO = ["Denver", "South / southeast suburbs", "West suburbs", "North suburbs"]
REDEEMED, SOLD = 105415, 139602          # 2025-26 ticket sales sheet, grand total

st.markdown(f"""
<style>
.block-container {{padding-top:0.4rem; padding-bottom:0.5rem; max-width:1500px;}}
header[data-testid="stHeader"] {{background:transparent;}}
.band {{background:{MAROON}; color:#F8F5EE; padding:8px 20px; border-radius:8px; margin-bottom:4px;}}
.band h1 {{color:#F8F5EE; font-size:1.4rem; margin:0; padding:0;}}
.band p {{color:{GOLD}; margin:0; font-size:.85rem;}}
.card {{background:{PANEL}; border:1px solid {BORDER}; border-radius:8px; padding:0 0 8px 0;
        box-shadow:2px 2px 4px rgba(0,0,0,.08); text-align:center; overflow:hidden;}}
.card .t {{background:{BORDER}; color:{TEXT}; font-size:.75rem; font-weight:600; padding:4px;}}
.card .v {{font-size:1.7rem; font-weight:600; color:{TEXT}; padding-top:4px; line-height:1.2;}}
.card .s {{font-size:.75rem; color:{MUTED};}}
.box {{background:{PANEL}; border:1px solid {BORDER}; border-radius:8px; padding:10px 16px; box-sizing:border-box; height:302px; overflow:hidden;}}
.box, .box h4, .box li {{color:{TEXT} !important;}}
.box h4 {{margin:0 0 4px 0; font-size:.95rem;}}
.box li {{margin-bottom:4px; font-size:.82rem;}}
.foot {{color:{MUTED}; font-size:.72rem; margin-top:4px;}}
div[data-testid="stPlotlyChart"] {{background:{PANEL}; border:1px solid {BORDER}; border-radius:8px; padding:0; overflow:hidden;}}
</style>""", unsafe_allow_html=True)


LABELS = {"Alum": "Alumni", "General fan": "General Fan", "Faculty/staff": "Faculty/Staff", "No answer": "No Answer",
          "South / southeast suburbs": "South / Southeast Suburbs", "West suburbs": "West Suburbs",
          "North suburbs": "North Suburbs", "Out of state": "Out of State"}
def nice(x):
    return LABELS.get(x, x)

@st.cache_data
def load():
    df = pd.read_csv("data/survey_clean.csv", dtype={"zip": str})
    df["region"] = df["region"].fillna("Unknown")
    return df

df = load()

# ---------- header + filters ----------
st.markdown("""<div class="band"><h1>DU Hockey Audience Profile</h1>
<p>Survey respondents and ticket holders, 2025-27</p></div>""", unsafe_allow_html=True)

f1, f2 = st.columns(2)
tix_opts = df["ticket_type"].dropna().unique().tolist()
rel_opts = ["Alum", "Parent", "General fan", "Student", "Faculty/staff"]
tix_sel = f1.multiselect("Ticket Type", tix_opts, placeholder="All Ticket Types", format_func=nice)
rel_sel = f2.multiselect("Relationship", rel_opts, placeholder="All Relationships", format_func=nice)

d_tix = df[df["ticket_type"].isin(tix_sel)] if tix_sel else df          # ticket filter only
d = d_tix[d_tix["rel_group"].isin(rel_sel)] if rel_sel else d_tix       # both filters

if d.empty:
    st.warning("No respondents match these filters.")
    st.stop()

def pct(a, b):
    return f"{a / b:.0%}" if b else "–"

# ---------- KPI measures (same logic as the Power BI DAX) ----------
n = len(d)
inc = d["Income Order"].dropna()
p100 = pct((inc >= 5).sum(), len(inc))
reg = d[d["region"] != "Unknown"]
metro = pct(reg["region"].isin(METRO).sum(), len(reg))
# Alumni & Parents ignores the Relationship filter, respects Ticket Type
ap = pct(d_tix["rel_group"].isin(["Alum", "Parent"]).sum(), len(d_tix))
redemption = pct(REDEEMED, SOLD)

cards = [("Respondents", f"{n:,}", "survey responses"),
         ("Earn $100K+", p100, f"of {len(inc):,} who answered"),
         ("Live in Denver Metro", metro, f"of {len(reg):,} with a known zip code"),
         ("Alumni & Parents", ap, "of ticket-type group"),
         ("Tickets Redeemed", redemption, "2025-26 season")]
for col, (t, v, s) in zip(st.columns(5), cards):
    col.markdown(f'<div class="card"><div class="t">{t}</div><div class="v">{v}</div>'
                 f'<div class="s">{s}</div></div>', unsafe_allow_html=True)

def style(fig, h=330, title=None):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=44 if title else 10, b=10),
                      paper_bgcolor=PANEL, plot_bgcolor=PANEL, font=dict(color=TEXT),
                      title=dict(text=title, x=0.02, font=dict(size=14)) if title else None,
                      showlegend=False)
    return fig

def donut(series, title):
    c = series.fillna("No answer").map(nice).value_counts().reset_index()
    c.columns = ["label", "n"]
    fig = go.Figure(go.Pie(labels=c["label"], values=c["n"], hole=0.55, sort=True,
                           marker=dict(colors=RAMP, line=dict(color=PANEL, width=2)),
                           textinfo="label+percent", textposition="outside"))
    fig = style(fig, 310, title)
    fig.update_layout(margin=dict(l=90, r=90, t=44, b=16))
    return fig

# ---------- row 2: donuts + income share ----------
c1, c2, c3 = st.columns([1.2, 1.2, 1.5])
c1.plotly_chart(donut(d["rel_group"], "Relationship to DU"), width="stretch")
c2.plotly_chart(donut(d["ticket_type"], "Ticket Type"), width="stretch")

# income: denominator = answered, ignoring nothing else (bars show share by band)
ic = d["income_band"].value_counts().reindex(INCOME_ORDER).fillna(0)
share = ic / ic.sum() if ic.sum() else ic
ifig = go.Figure(go.Bar(x=share.values, y=INCOME_ORDER, orientation="h", marker_color=MAROON,
                        text=[f"{v:.0%}" for v in share.values], textposition="outside"))
ifig.update_yaxes(autorange="reversed"); ifig.update_xaxes(visible=False, range=[0, max(share.max() * 1.25, .1)])
c3.plotly_chart(style(ifig, 310, "Income Share"), width="stretch")


# ---------- row 3: regions + map + takeaways ----------
c4, c5, c6 = st.columns([1, 1.4, 1])

rc = reg["region"].map(nice).value_counts().sort_values()
rfig = go.Figure(go.Bar(x=rc.values, y=rc.index, orientation="h", marker_color=MAROON,
                        text=rc.values, textposition="outside"))
rfig.update_xaxes(visible=False, range=[0, rc.max() * 1.2])
c4.plotly_chart(style(rfig, 300, "Respondents by Region"), width="stretch")

# map: one street map with state outlines; the buttons live inside the chart, next to the title
pts = (d.dropna(subset=["lat", "long"]).groupby(["zip", "lat", "long"]).size()
       .reset_index(name="n"))
with open("data/us_states.json") as f:
    states = json.load(f)
mfig = px.scatter_map(pts, lat="lat", lon="long", size="n", hover_name="zip",
                      hover_data={"n": True, "lat": False, "long": False},
                      labels={"n": "Respondents", "zip": "Zip code"},
                      size_max=28, color_discrete_sequence=[MAROON])
mfig.update_traces(marker=dict(opacity=.6),
                   hovertemplate="<b>Zip Code = %{hovertext}</b><br>Respondents = %{customdata[0]}<extra></extra>")
DENVER = dict(center=dict(lat=39.68, lon=-104.95), zoom=8.3)
US = dict(center=dict(lat=38.5, lon=-96.5), zoom=2.9)
mfig = style(mfig, 300, "Respondents by Zip Code")
mfig.update_layout(
    title=dict(y=1 - 25 / 300, yref="container", yanchor="middle"),   # title centered 25px from the top
    margin=dict(l=0, r=0, t=50, b=0),
    map=dict(style="carto-positron", layers=[dict(sourcetype="geojson", source=states, type="line",
                                                  color="#8A8272", line=dict(width=1))], **DENVER),
    updatemenus=[dict(type="buttons", direction="right", active=0, x=0, xanchor="left", pad=dict(l=185, t=0, b=0, r=0), y=1.1, yanchor="middle",
                      bgcolor=PANEL, bordercolor=BORDER, font=dict(size=11, color=TEXT),
                      buttons=[dict(label="Denver Area", method="relayout",
                                    args=[{"map.center": DENVER["center"], "map.zoom": DENVER["zoom"]}]),
                               dict(label="Entire US", method="relayout",
                                    args=[{"map.center": US["center"], "map.zoom": US["zoom"]}])])])
c5.plotly_chart(mfig, width="stretch")

# takeaways: computed from the filtered data so they never go stale
def take():
    def metro_pct(x):
        r = x[x["region"] != "Unknown"]
        return pct(r["region"].isin(METRO).sum(), len(r))
    def hi_pct(x):
        i = x["Income Order"].dropna()
        return pct((i >= 5).sum(), len(i))
    def ap_pct(x):
        return pct(x["rel_group"].isin(["Alum", "Parent"]).sum(), len(x))
    fs = df[df["ticket_type"] == "Full/Half Season"]
    sg = df[df["ticket_type"] == "Single Game"]
    mp = df[df["ticket_type"] == "5-Game/Mini-Plan"]
    return [
        f"{metro_pct(fs)} of full/half-season holders live in the Denver metro, vs {metro_pct(sg)} of single-game buyers.",
        f"Plan holders earn more: {hi_pct(mp)} of mini-plan and {hi_pct(fs)} of full/half-season holders earn $100K+, vs {hi_pct(sg)} of single-game buyers.",
        f"{ap_pct(fs)} of full/half-season holders are alumni or parents, vs {ap_pct(sg)} of single-game buyers.",
        f"Parents are the most spread out: only {metro_pct(df[df['rel_group'] == 'Parent'])} live in the Denver metro, vs {metro_pct(df[df['rel_group'] == 'Alum'])} of alumni.",
    ]
li = "".join(f"<li>{t}</li>" for t in take())
c6.markdown(f'<div class="box"><h4>Key Takeaways</h4><ul>{li}</ul></div>', unsafe_allow_html=True)

st.markdown(f"""<div class="foot">Source: DU Athletics fan survey ({len(df):,} respondents) and 2025-27 ticket data.
Survey respondents are self-selected; income and region shares use only respondents who answered.
Redemption rate is season-wide and does not change with filters.</div>""", unsafe_allow_html=True)
