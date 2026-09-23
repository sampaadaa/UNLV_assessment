"""Build the Part 1 research summary memo (PDF) from report_assets figures + hardcoded, notebook-verified numbers."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 Image, HRFlowable, ListFlowable, ListItem, KeepTogether)
from PIL import Image as PILImage

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS_DIR = os.path.dirname(HERE)
DETAILED_DIR = os.path.dirname(BUILD_SCRIPTS_DIR)   # documents/detailed_explanation/
OUT = os.path.join(DETAILED_DIR, "Part1_Detailed_Report.pdf")

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

MAROON = colors.HexColor("#7a1f2b")
DARKGRAY = colors.HexColor("#333333")
LIGHTGRAY = colors.HexColor("#f2f2f2")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("MemoTitle", parent=styles["Title"], fontSize=15, textColor=MAROON,
                           spaceAfter=2, alignment=TA_LEFT))
styles.add(ParagraphStyle("MemoSub", parent=styles["Normal"], fontSize=9, textColor=DARKGRAY, spaceAfter=8))
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=12.5, textColor=MAROON,
                           spaceBefore=12, spaceAfter=4))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10.5, textColor=colors.black,
                           spaceBefore=8, spaceAfter=3))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.3, leading=12.5, spaceAfter=5))
styles.add(ParagraphStyle("BulletTxt", parent=styles["Normal"], fontSize=9.3, leading=12.3, spaceAfter=2))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8, textColor=DARKGRAY,
                           alignment=TA_CENTER, spaceAfter=8, spaceBefore=2))
styles.add(ParagraphStyle("TblHead", parent=styles["Normal"], fontSize=8.3, textColor=colors.white,
                           fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("TblCell", parent=styles["Normal"], fontSize=8.3, leading=10.5))

story = []


def para(text, style="Body"):
    story.append(Paragraph(text, styles[style]))


def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(it, styles["BulletTxt"]), leftIndent=10, bulletColor=MAROON) for it in items],
        bulletType="bullet", start="•", leftIndent=8, spaceBefore=2, spaceAfter=6,
    ))


def rule():
    story.append(HRFlowable(width="100%", thickness=0.75, color=MAROON, spaceBefore=2, spaceAfter=8))


def fig(path, width_in, caption):
    im = PILImage.open(os.path.join(HERE, os.path.basename(path)))
    w, h = im.size
    width = width_in * inch
    height = width * (h / w)
    story.append(Image(os.path.join(HERE, os.path.basename(path)), width=width, height=height))
    story.append(Paragraph(caption, styles["Caption"]))


def make_table(header, rows, col_widths=None, font_size=8.3, align_cols=None):
    data = [[Paragraph(f"<b>{h}</b>", styles["TblHead"]) for h in header]]
    for r in rows:
        data.append([Paragraph(str(c), styles["TblCell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), MAROON),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHTGRAY]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if align_cols:
        for c in align_cols:
            style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


# ============================== HEADER ==============================
para("Technical Memorandum, Part 1: Capital Bikeshare Demand Analysis &amp; Forecasting", "MemoTitle")
para("University of Nevada, Las Vegas &nbsp;|&nbsp; Dept. of Civil and Environmental Engineering and "
     "Construction &nbsp;|&nbsp; Dr. Sohn&rsquo;s Research Lab", "MemoSub")

hdr = Table([
    [Paragraph("<b>TO:</b>", styles["TblCell"]), Paragraph("Dr. Sohn&rsquo;s Research Lab, PhD Technical Assessment Review", styles["TblCell"])],
    [Paragraph("<b>FROM:</b>", styles["TblCell"]), Paragraph("Sampada Kharel (sampadha.kharel@gmail.com)", styles["TblCell"])],
    [Paragraph("<b>DATE:</b>", styles["TblCell"]), Paragraph("September 22, 2026", styles["TblCell"])],
    [Paragraph("<b>RE:</b>", styles["TblCell"]), Paragraph("Part 1 findings: descriptive statistics, regression analysis, and demand forecasting "
                                                            "(full code: <i>part1_bikeshare.ipynb</i>)", styles["TblCell"])],
], colWidths=[0.7 * inch, CONTENT_W - 0.7 * inch])
hdr.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHTGRAY),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(hdr)
rule()

# ============================== DATA & METHODS ==============================
para("<b>Data &amp; Methodology.</b> This analysis uses the UCI Bike Sharing dataset (<i>hour.csv</i>, 17,379 "
     "hourly records, Washington D.C., 2011&ndash;2012). Weather variables were denormalized using the UCI "
     "web page&rsquo;s min-max formulas (temp: &minus;8&ndash;39&deg;C; atemp: &minus;16&ndash;50&deg;C). "
     "<b>Season codes were corrected</b> to match the observed calendar months (1=winter&hellip;4=fall) rather than "
     "the assessment brief&rsquo;s labels, which are off by one step. The dataset is missing 165 of 17,544 possible "
     "hours; because no observed row has count = 0 and gaps cluster at night and during Hurricane Sandy, the "
     "January 2011 snowstorm, and Hurricane Irene, missing hours are treated as unrecorded zero-rental hours "
     "for feature construction; the main analysis and all reported metrics use observed hours only.", "Body")

# ============================== TASK 1 ==============================
para("Task 1: Descriptive Statistics &amp; Exploratory Analysis", "H1")
bullets([
    "<b>Overdispersion:</b> mean hourly count &asymp; 189, variance &asymp; 32,900. Variance far exceeds the "
    "mean for count, casual, and registered rentals, ruling out a simple Gaussian/Poisson-equidispersed model.",
    "<b>Hour &times; workingday interaction:</b> workdays show a sharp bimodal commute pattern (peaks at 08:00 and "
    "17&ndash;18:00); weekends/holidays show one broad midday peak: two qualitatively different daily shapes.",
    "<b>Casual vs. registered:</b> casual (leisure) demand is far more weekend- and weather-sensitive (weekend mean "
    "58.7 vs. weekday mean 26.3 rentals/hr); registered (commuter) demand peaks on workday commute hours. Casual "
    "share of total rentals swings from &asymp;9% at commute hours to &asymp;26% in the afternoon.",
    "<b>Year-over-year growth:</b> mean demand rose from 143.8 (2011) to 234.7 (2012) rentals/hour, a 63% increase, "
    "so any forecasting model must represent this trend.",
    "<b>Data-quality anomalies:</b> weather category 4 has only 3 hours; windspeed = 0 in 12.5% of hours (likely a "
    "sensor floor, not true calm air); a single day (2011-03-10) has humidity = 0 (sensor fault).",
])
fig("fig1_hourly_profiles.png", 6.6, "Figure 1. (a) Mean hourly demand by day type; (b) casual vs. registered rentals by hour.")

# ============================== TASK 2 ==============================
para("Task 2: Statistical &amp; Regression Analysis", "H1")
para("Models were built in stages to isolate each statistical issue named in the assessment: an OLS model on "
     "log(count+1) exposes multicollinearity and non-linearity; moving to Poisson, then Negative Binomial, GLMs "
     "addresses the count-data distribution directly.", "Body")

para("Multicollinearity, non-linearity, and overdispersion", "H2")
story.append(make_table(
    ["Diagnostic", "Result", "Action taken"],
    [
        ["VIF: temp vs. atemp", "43.6 / 43.7 (both) &rarr; 1.0 (temp alone)", "Dropped atemp"],
        ["Non-linearity (temp)", "AIC 31,260 &rarr; 30,846 adding temp&sup2;", "Quadratic term retained (p&lt;0.001)"],
        ["Hour &times; workingday", "AIC 30,846 &rarr; 14,755 adding interaction", "Interaction retained (F-test p&asymp;0)"],
        ["Overdispersion test", "Cameron-Trivedi est. &alpha;=0.041, t=35.0, p&asymp;0", "Negative Binomial (2-step) preferred over Poisson"],
        ["NB model fit", "AIC: Poisson 327,627 vs. NB2 175,749", "NB2 used for count"],
        ["Residual autocorrelation", "Durbin-Watson = 0.83; HAC/naive SE ratio &asymp;1.26&times;", "HAC (Newey-West, 24-lag) SEs reported"],
    ],
    col_widths=[1.5 * inch, 2.6 * inch, 2.4 * inch],
))
story.append(Spacer(1, 6))
para("<i>Note: the joint-MLE Negative Binomial failed to converge on this design (too many sparse dummy cells); "
     "the Cameron-Trivedi two-step estimator (Poisson &rarr; auxiliary OLS for &alpha; &rarr; GLM-NB with fixed "
     "&alpha;) was used instead and converges cleanly.</i>", "Body")

fig("fig2_temp_nonlinear.png", 3.3, "Figure 2. Demand rises with temperature, then flattens/declines, motivating the quadratic term.")

para("Casual vs. registered: incidence rate ratios (selected terms, Negative Binomial)", "H2")
story.append(make_table(
    ["Term", "Casual IRR", "p", "Registered IRR", "p"],
    [
        ["workingday", "0.45", "&lt;0.001", "0.99", "0.092"],
        ["holiday", "0.82", "&lt;0.001", "0.79", "&lt;0.001"],
        ["temp (&deg;C)", "1.18", "&lt;0.001", "1.06", "&lt;0.001"],
        ["weather = adverse (3)", "0.53", "&lt;0.001", "0.62", "&lt;0.001"],
        ["year = 2012", "1.36", "&lt;0.001", "1.63", "&lt;0.001"],
    ],
    col_widths=[1.7 * inch, 1.1 * inch, 0.7 * inch, 1.3 * inch, 0.7 * inch],
    align_cols=[1, 2, 3, 4],
))
story.append(Spacer(1, 6))
bullets([
    "Workday status roughly <b>halves casual demand</b> (IRR 0.45) but has a small, non-significant marginal effect "
    "on registered demand once hour is controlled for. The registered commute signature lives in "
    "<i>which hours</i> are busy (the hour&times;workingday interaction above), not the daily level.",
    "Casual demand is more weather-sensitive (IRR 0.53 vs. 0.62 in adverse weather) and grew more slowly "
    "year-over-year (IRR 1.36 vs. 1.63) than registered demand, consistent with membership-driven growth.",
    "Variable selection combined domain reasoning, nested-model AIC/F-tests (above), and a LassoCV robustness "
    "check that retained the same features (temp, temp&sup2;, hour, and weather dummies dominate by magnitude).",
])

# ============================== TASK 3 ==============================
para("Task 3: Demand Forecasting &amp; Predictive Modeling", "H1")
para("<b>Split:</b> train = days 1&ndash;20 of each month (11,460 hours); test = day 21&ndash;month end "
     "(5,919 hours; 24 monthly windows), as prescribed. <b>Leakage design:</b> the longest test window is 264 "
     "hours, so any feature lag under 264 hours can reference a timestamp inside the very window being predicted, "
     "verified both analytically and with an executable check. All history-derived features use a "
     "336-hour (2-week) lag or longer, and a demonstration confirms a naive 24-hour lag would leak into 5,448 of "
     "6,024 test hours, while 336 hours leaks into none. <b>Two scenarios</b> are reported: (A) strict, "
     "calendar + history features only (realistic case); (B) oracle weather, adds true future weather as "
     "an upper bound. <b>Features:</b> hour/day/month/year, cyclical encodings, workingday/holiday/rush-hour "
     "flags, a day-index trend, and three leakage-safe history features (a 336h lag, a 4&ndash;7 week average, "
     "and an expanding same-hour-of-week mean).", "Body")

para("Model comparison (test-set RMSLE, primary metric)", "H2")
story.append(make_table(
    ["Model", "Scenario", "RMSLE", "MAE", "RMSE"],
    [
        ["Seasonal-mean baseline", "A (strict)", "0.651", "79.4", "118.9"],
        ["Poisson GLM", "A", "0.580", "54.0", "90.2"],
        ["Random Forest", "A", "0.536", "47.3", "80.5"],
        ["<b>LightGBM (Poisson)</b>", "<b>A</b>", "<b>0.531</b>", "<b>47.5</b>", "<b>81.5</b>"],
        ["Poisson GLM", "B (oracle weather)", "0.472", "41.1", "68.8"],
        ["Random Forest", "B", "0.472", "38.8", "66.3"],
        ["<b>LightGBM (Poisson)</b>", "<b>B</b>", "<b>0.440</b>", "<b>34.3</b>", "<b>59.2</b>"],
    ],
    col_widths=[1.7 * inch, 1.3 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch],
    align_cols=[2, 3, 4],
))
story.append(Spacer(1, 6))

fig("fig3_model_comparison.png", 5.0, "Figure 3. Test RMSLE by model and scenario.")
fig("fig4_per_window.png", 6.6, "Figure 4. Per-window RMSLE, best strict model (LightGBM, Scenario A).")

bullets([
    "LightGBM (Poisson objective) is the best model in both scenarios, beating the seasonal-mean baseline by "
    "&asymp;18% and the naive 2-week-lag baseline similarly on RMSLE.",
    "Knowing future weather (Scenario B) improves RMSLE by a further &asymp;17% (0.531 &rarr; 0.440), quantifying "
    "how much realistic-case error is attributable to weather uncertainty rather than the model itself.",
    "<b>Worst-performing windows</b> (Dec 2012, RMSLE 1.18; Dec 2011; Nov 2012) coincide with the largest "
    "within-month demand-level shifts (e.g., Dec 2012 mean demand fell 63% from the training to the test portion "
    "of the month), not with the Sandy/Irene storm windows. A strong correlation (r = 0.75) links per-window "
    "error to this level shift. History-based features cannot anticipate a seasonal regime change.",
    "A fully sequential <b>rolling-origin backtest</b> (training only on data prior to each window) gives RMSLE "
    "0.544, close to the prescribed split&rsquo;s 0.531, supporting the headline result despite the "
    "prescribed split&rsquo;s known chronology quirk (it pools all months&rsquo; first 20 days regardless of order).",
])

# ============================== LIMITATIONS ==============================
para("Limitations &amp; Conclusion", "H1")
bullets([
    "Missing-hour imputation (zero rentals) is inferred, not documented in the source; a sensitivity check "
    "excluding these hours from feature history was not exhaustively re-verified beyond the checks in Section 3.",
    "The prescribed train/test split allows later months to inform earlier test windows; the rolling-origin "
    "backtest addresses this but was only evaluated for the single best Scenario-A model.",
    "No classical time-series model (SARIMAX/Prophet) was fit as a further comparison, given time constraints; "
    "the tree/GLM comparison presented is considered sufficient to support the conclusions above.",
])
para("Overall, the dataset shows strong, well-understood seasonal and behavioral structure (commute vs. leisure "
     "usage, overdispersed counts, temperature non-linearity), which a Negative Binomial GLM explains well for "
     "inference, and which a leakage-safe LightGBM model forecasts with a realistic RMSLE of 0.53, a "
     "meaningful, verified improvement over naive baselines, with weather uncertainty and seasonal regime shifts "
     "identified as the two main remaining error sources.", "Body")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DARKGRAY)
    canvas.drawString(MARGIN, 0.45 * inch, "UNLV PhD Technical Assessment, Part 1 Research Summary")
    canvas.drawRightString(PAGE_W - MARGIN, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=letter,
                         leftMargin=MARGIN, rightMargin=MARGIN, topMargin=0.6 * inch, bottomMargin=0.7 * inch,
                         title="Part 1 Research Summary Report", author="Sampada Kharel")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
