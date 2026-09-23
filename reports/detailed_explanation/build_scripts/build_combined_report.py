"""Build the combined, concise Technical Assessment Report (Part 1 + Part 2) for submission.

This is the main deliverable sent to the reviewer. It does not reference the internal PART1_PLAN.md /
PART2_PLAN.md planning documents (those, along with the fuller per-part reports and training logs, live in
documents/detailed_explanation/ and are not part of this file). Figures are reused from the existing
report_assets / report_assets_p2 folders rather than regenerated.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 Image, HRFlowable, ListFlowable, ListItem, KeepTogether)
from PIL import Image as PILImage

HERE = os.path.dirname(os.path.abspath(__file__))              # documents/detailed_explanation/build_scripts/
FIG1 = os.path.join(HERE, "report_assets")
FIG2 = os.path.join(HERE, "report_assets_p2")
DOCUMENTS_DIR = os.path.dirname(os.path.dirname(HERE))          # documents/
OUT = os.path.join(DOCUMENTS_DIR, "Technical_Assessment_Report.pdf")

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
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13, textColor=MAROON,
                           spaceBefore=12, spaceAfter=4))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10.5, textColor=colors.black,
                           spaceBefore=7, spaceAfter=3))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.2, leading=12.2, spaceAfter=5))
styles.add(ParagraphStyle("BulletTxt", parent=styles["Normal"], fontSize=9.2, leading=12.0, spaceAfter=2))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=7.8, textColor=DARKGRAY,
                           alignment=TA_CENTER, spaceAfter=7, spaceBefore=2))
styles.add(ParagraphStyle("TblHead", parent=styles["Normal"], fontSize=8, textColor=colors.white,
                           fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("TblCell", parent=styles["Normal"], fontSize=8, leading=10))

story = []


def para(text, style="Body"):
    story.append(Paragraph(text, styles[style]))


def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(it, styles["BulletTxt"]), leftIndent=10, bulletColor=MAROON) for it in items],
        bulletType="bullet", start="•", leftIndent=8, spaceBefore=2, spaceAfter=5,
    ))


def rule():
    story.append(HRFlowable(width="100%", thickness=0.75, color=MAROON, spaceBefore=2, spaceAfter=8))


def fig(folder, name, width_in, caption):
    p = os.path.join(folder, name)
    im = PILImage.open(p)
    w, h = im.size
    width = width_in * inch
    height = width * (h / w)
    story.append(Image(p, width=width, height=height))
    story.append(Paragraph(caption, styles["Caption"]))


def make_table(header, rows, col_widths=None, font_size=8, align_cols=None):
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
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if align_cols:
        for c in align_cols:
            style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


# ============================== HEADER ==============================
para("Technical Assessment Report: Time Series Forecasting &amp; Computer Vision", "MemoTitle")
para("University of Nevada, Las Vegas &nbsp;|&nbsp; Dept. of Civil and Environmental Engineering and "
     "Construction &nbsp;|&nbsp; Dr. Sohn&rsquo;s Research Lab", "MemoSub")

hdr = Table([
    [Paragraph("<b>TO:</b>", styles["TblCell"]), Paragraph("Dr. Sohn&rsquo;s Research Lab, PhD Technical Assessment Review", styles["TblCell"])],
    [Paragraph("<b>FROM:</b>", styles["TblCell"]), Paragraph("Sampada Kharel (sampadha.kharel@gmail.com)", styles["TblCell"])],
    [Paragraph("<b>DATE:</b>", styles["TblCell"]), Paragraph("September 23, 2026", styles["TblCell"])],
    [Paragraph("<b>RE:</b>", styles["TblCell"]), Paragraph("Part 1: Capital Bikeshare Demand Analysis &amp; Forecasting; "
                                                            "Part 2: Building Footprint Segmentation "
                                                            "(full code: <i>part1_bikeshare.ipynb</i>, <i>part2_segmentation.ipynb</i>)", styles["TblCell"])],
], colWidths=[0.7 * inch, CONTENT_W - 0.7 * inch])
hdr.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHTGRAY),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(hdr)
rule()

# ============================================================================================
# PART 1
# ============================================================================================
para("Part 1: Capital Bikeshare Demand Analysis &amp; Forecasting", "H1")

para("<b>Data.</b> UCI Bike Sharing dataset (17,379 hourly records, Washington D.C., 2011&ndash;2012). Weather "
     "variables were denormalized to physical units; season codes were corrected to match the observed calendar "
     "months, since the raw coding is off by one step from the actual dates.", "Body")

para("Descriptive statistics &amp; exploratory analysis", "H2")
bullets([
    "Demand is overdispersed (mean &asymp; 189, variance &asymp; 32,900 for hourly count), ruling out a simple "
    "Gaussian or equidispersed-Poisson model.",
    "Workdays show a sharp bimodal commute pattern (peaks at 08:00 and 17&ndash;18:00); weekends/holidays show one "
    "broad midday peak.",
    "Casual (leisure) demand is far more weekend- and weather-sensitive than registered (commuter) demand; casual "
    "share of total rentals swings from &asymp;9% at commute hours to &asymp;26% in the afternoon.",
    "Demand grew 63% from 2011 to 2012, requiring a trend/year term in any forecasting model.",
])
fig(FIG1, "fig1_hourly_profiles.png", 6.4, "Figure 1. Hourly demand by day type, and casual vs. registered by hour.")

para("Statistical &amp; regression analysis", "H2")
para("Models were built in stages to address each statistical issue directly: an OLS model on log(count+1) "
     "surfaces multicollinearity and non-linearity; moving to a Negative Binomial GLM addresses the count-data "
     "distribution.", "Body")
story.append(make_table(
    ["Diagnostic", "Result", "Action taken"],
    [
        ["Multicollinearity (temp vs. atemp)", "VIF 43.6 / 43.7 together, 1.0 apart", "Dropped atemp"],
        ["Non-linearity (temperature)", "AIC improves 31,260 to 30,846 adding temp²", "Quadratic term retained"],
        ["Hour x workingday interaction", "AIC improves to 14,755 adding it", "Interaction retained (F-test p&asymp;0)"],
        ["Count distribution", "Overdispersion confirmed (Cameron-Trivedi test, p&asymp;0)", "Negative Binomial GLM used"],
        ["Residual autocorrelation", "Durbin-Watson = 0.83", "HAC (Newey-West) standard errors used"],
    ],
    col_widths=[1.7 * inch, 2.6 * inch, 2.2 * inch],
))
story.append(Spacer(1, 5))
para("Casual and registered users were modeled separately as the assessment allows, using incidence rate ratios "
     "(IRR) from a Negative Binomial fit.", "Body")
story.append(make_table(
    ["Term", "Casual IRR", "p", "Registered IRR", "p"],
    [
        ["workingday", "0.45", "&lt;0.001", "0.99", "0.092"],
        ["holiday", "0.82", "&lt;0.001", "0.79", "&lt;0.001"],
        ["temp (&deg;C)", "1.18", "&lt;0.001", "1.06", "&lt;0.001"],
        ["weather = adverse (3)", "0.53", "&lt;0.001", "0.62", "&lt;0.001"],
        ["year = 2012", "1.36", "&lt;0.001", "1.63", "&lt;0.001"],
    ],
    col_widths=[1.7 * inch, 1.1 * inch, 0.65 * inch, 1.3 * inch, 0.65 * inch],
    align_cols=[1, 2, 3, 4],
))
story.append(Spacer(1, 5))
para("Workday status roughly halves casual demand (IRR 0.45) but has little marginal effect on registered demand "
     "once hour is controlled for; the registered commute signature lives in which hours are busy, not the daily "
     "total. Casual demand is also more weather-sensitive (IRR 0.53 vs. 0.62 in adverse weather) and grew more "
     "slowly year-over-year (IRR 1.36 vs. 1.63), consistent with membership-driven growth in registered "
     "ridership. Variable selection combined domain reasoning, nested-model AIC/F-tests, and a LassoCV robustness "
     "check that agreed with the chosen features.", "Body")

para("Demand forecasting", "H2")
para("<b>Split (as prescribed):</b> train = days 1&ndash;20 of each month (11,460 hours); test = day "
     "21&ndash;month end (5,919 hours, 24 monthly windows). <b>Leakage prevention:</b> the longest test window is "
     "264 hours, so any feature lag under 264 hours could reference a timestamp inside the window being "
     "predicted; all history-derived features use a 336-hour (2-week) lag or longer, verified with an executable "
     "check that no test-row feature reaches into its own test window. Two scenarios are reported: (A) strict, "
     "calendar and history features only (the realistic case); (B) oracle weather, which adds true future weather "
     "as an upper bound.", "Body")
story.append(make_table(
    ["Model", "Scenario", "RMSLE", "MAE", "RMSE"],
    [
        ["Seasonal-mean baseline", "A (strict)", "0.651", "79.4", "118.9"],
        ["Poisson GLM", "A", "0.580", "54.0", "90.2"],
        ["Random Forest", "A", "0.536", "47.3", "80.5"],
        ["<b>LightGBM (Poisson)</b>", "<b>A</b>", "<b>0.531</b>", "<b>47.5</b>", "<b>81.5</b>"],
        ["LightGBM (Poisson)", "B (oracle weather)", "0.440", "34.3", "59.2"],
    ],
    col_widths=[1.8 * inch, 1.4 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch],
    align_cols=[2, 3, 4],
))
story.append(Spacer(1, 5))
fig(FIG1, "fig4_per_window.png", 6.4, "Figure 2. Per-window RMSLE across all 24 evaluation windows, best strict model.")
bullets([
    "LightGBM with a Poisson objective is the best model in both scenarios, beating the seasonal-mean baseline by "
    "&asymp;18% on RMSLE; knowing future weather improves RMSLE a further &asymp;17%, quantifying the cost of "
    "weather uncertainty in the realistic case.",
    "The worst windows (December of both years) coincide with the largest within-month demand-level shifts "
    "(winter onset, holidays), not the Hurricane Sandy/Irene storm windows, which a lag-based model handles fine "
    "since they are brief. A correlation of r=0.75 links per-window error to this level shift.",
    "A fully sequential rolling-origin backtest (training only on data prior to each window) gives RMSLE 0.544, "
    "close to the prescribed split's 0.531, supporting the headline result.",
])

story.append(Spacer(1, 4))

# ============================================================================================
# PART 2
# ============================================================================================
para("Part 2: Building Footprint Segmentation", "H1")

para("<b>Data &amp; scope.</b> Inria Aerial Image Labeling dataset: 5000&times;5000 px, 0.3 m RGB tiles with "
     "binary building masks. The official test split has no public masks, so the 180 labeled train tiles were "
     "partitioned independently. For time/compute reasons, a representative subset of 40 tiles (8 per city "
     "&times; 5 cities) was used, disclosed explicitly.", "Body")

para("Data partitioning and leakage prevention", "H2")
para("Each tile is cut into a non-overlapping 9&times;9 grid of 512&times;512 patches; no two patches can share a "
     "pixel, by construction, which rules out the overlapping-patch leakage mode by design. Two splits are used, "
     "both verified with executable assertions: a <b>primary split</b> (tile-disjoint, per-city-proportional: 6 "
     "train / 1 val / 1 test tile per city) for the headline result, and a <b>leave-one-city-out split</b> "
     "(Kitsap held out entirely, never seen in training or validation) as a direct, quantified probe of "
     "geographic leakage across cities.", "Body")

para("Model and loss", "H2")
para("U-Net with a ResNet34 encoder pretrained on ImageNet: skip connections preserve the fine edge detail a "
     "plain classifier would lose, and the pretrained encoder speeds convergence given the reduced data budget. "
     "The loss is <b>0.4&times;BCE + 0.4&times;Dice + 0.2&times;BoundaryDice</b>. Dice optimizes overlap and is "
     "robust to class imbalance (buildings cover 0.2%&ndash;46.4% of pixels depending on city); BCE gives a "
     "stable gradient; BoundaryDice is a Dice loss restricted to a narrow band around the ground-truth boundary, "
     "which targets edge precision directly in the loss rather than only measuring it afterward.", "Body")

para("Quantitative results", "H2")
story.append(make_table(
    ["Eval set", "IoU", "Dice", "Precision", "Recall", "PixelAcc", "BoundaryIoU"],
    [
        ["Primary (unseen tiles, known cities)", "0.770", "0.870", "0.848", "0.893", "94.8%", "0.564"],
        ["Leave-one-city-out (Kitsap, never seen)", "0.677", "0.808", "0.853", "0.767", "99.4%", "0.518"],
    ],
    col_widths=[2.3 * inch, 0.6 * inch, 0.6 * inch, 0.75 * inch, 0.6 * inch, 0.75 * inch, 0.85 * inch],
    align_cols=[1, 2, 3, 4, 5, 6],
))
story.append(Spacer(1, 5))
para("Pixel accuracy alone would be misleading here (a trivial all-background prediction already scores 99.8% on "
     "the sparsest tile), which is why IoU, Dice, precision/recall, and boundary metrics are reported instead. "
     "Evaluating the same held-out city (Kitsap) once with a model that saw other tiles of that city and once "
     "with a model that never saw it at all shows an IoU drop of 0.139 (17% relative), the direct, quantified "
     "answer to the geographic-leakage question.", "Body")

fig(FIG2, "fig5_percity.png", 4.4, "Figure 3. Test IoU by city (primary split).")
para("Counter-intuitively, sparse/rural Kitsap has the highest in-distribution IoU of all five cities, not the "
     "lowest: isolated, high-contrast rooftops against forest/field are an easy case despite little training "
     "signal. Chicago and Vienna, the densest cities, are hardest in-distribution.", "Body")

para("Qualitative visual assessment", "H2")
fig(FIG2, "fig6_best.png", 5.0, "Figure 4. Best predictions: two Kitsap patches and one Tyrol-w patch, isolated "
                                 "rural buildings against a plain background.")
fig(FIG2, "fig7_worst.png", 5.0, "Figure 5. Worst predictions: Austin and Chicago. A large non-building structure "
                                  "mistaken for a rooftop, small structures only partially detected, and a dense "
                                  "complex with mixed correct and incorrect detections.")

para("Adding the boundary term improved Boundary-IoU on every city relative to a BCE+Dice-only loss, confirming "
     "it had the intended effect rather than only adding complexity. Typical patches in dense cities are correct "
     "at the block level but scatter errors along the edges between adjacent buildings, a modest instance-"
     "adjacency effect expected of semantic (not instance) segmentation.", "Body")

story.append(KeepTogether([
    Paragraph("Conclusion", styles["H1"]),
    Paragraph(
        "Both parts follow the same standard: leakage prevention verified by executable assertion rather than "
        "assumed, model and metric choices matched to the data's known statistical issues, and results reported "
        "with an honest breakdown across evaluation windows or cities rather than a single aggregate number. "
        "Part 1 delivers a leakage-safe forecasting model with RMSLE 0.531 on the prescribed split, confirmed by "
        "a rolling-origin backtest. Part 2 delivers a segmentation model with test IoU 0.770, and the "
        "leave-one-city-out experiment gives a concrete, quantified answer to the assessment's central "
        "geographic-leakage question: a 17% relative IoU drop when a city's visual style has never been seen.",
        styles["Body"],
    ),
]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DARKGRAY)
    canvas.drawString(MARGIN, 0.4 * inch, "UNLV PhD Technical Assessment, Technical Report")
    canvas.drawRightString(PAGE_W - MARGIN, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=letter,
                         leftMargin=MARGIN, rightMargin=MARGIN, topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                         title="Technical Assessment Report", author="Sampada Kharel")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
