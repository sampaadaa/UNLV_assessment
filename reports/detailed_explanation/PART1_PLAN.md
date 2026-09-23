# Part 1 Plan: Capital Bikeshare Demand Analysis & Forecasting

Decision log and roadmap for Part 1 of the UNLV (Dr. Sohn) technical assessment. **Deadline: 2026-09-25.**
Later Part 1 decisions should be checked against this file and, when they change, recorded here (see §10).

**Target level: "Tier 2"**, meaning PhD-application quality. That goes beyond a minimal submission with rigorous diagnostics, leakage-safe forecasting and honest error analysis.

---

## 1. What the task demands

**Input:** UCI Bike Sharing dataset, `dataset/hour.csv` (Washington D.C., hourly, 2011-01-01 to 2012-12-31).

**Deliverables (shared with Part 2):**
1. An executable Jupyter notebook (.ipynb) with annotated code for data loading, EDA, regression and the forecasting pipeline.
2. A concise research memo (.pdf) with statistical findings, regression tables, forecasting metrics and reasoning.

| Task | Requirement | Required output |
|---|---|---|
| **1. Descriptive stats / EDA** | Find noteworthy patterns and anomalies, such as rentals by time window and weather, and casual vs registered behaviour | Plots, tables, written insights |
| **2. Statistical / regression analysis** | Regress `count`, `casual` or `registered` on predictors. Discuss findings, **variable selection logic**, and **statistical issues** (multicollinearity, non-linearity, count-data distribution) | Regression tables, diagnostics, discussion |
| **3. Forecasting** | **Do the split yourself:** train = days 1–20 of each month, test = day 21 to month end. Predict hourly `count` on the test windows. **All features must use only information available before each prediction period** (no lookahead / leakage). | Metric choice, feature engineering, model + training setup, results across evaluation windows |

---

## 2. Data findings and decisions (verified on `hour.csv`)

| Finding | Detail | Decision |
|---|---|---|
| Schema differs from PDF | UCI uses `dteday`, `hr`, `weathersit`, `cnt`, `hum`, `yr`, `mnth`. The PDF lists Kaggle names (`datetime`, `weather`, `count`, `humidity`). | Build a `datetime` column (`dteday` + `hr`) and rename to PDF names. State the mapping in the notebook. |
| Values are normalized | `temp`, `atemp`, `hum`, `windspeed` are scaled to [0,1]. Max `temp` = 1.0. | Denormalize per the **UCI web page** (the local Readme's "divide by 41 / 50" is the daily-scale rule and doesn't fit the hourly data): `temp_C = temp×47 − 8` (min-max, −8…39 °C), `atemp_C = atemp×66 − 16` (−16…50 °C), `humidity = hum×100`, `windspeed = windspeed×67`. Check on the data: temp spans −7.1…39.0 °C, and atemp spans exactly −16…50 °C. Report units in °C and %, and the dataset's unspecified wind unit as-is. |
| Size | 17,379 rows, 2 years, 731 days. | Confirm the row count after cleaning. |
| **Missing hours** | The full hourly grid has 17,544 hours. **165 are absent** (76 days have < 24 rows, 75 gap runs). **No row has `cnt = 0` (min = 1).** The gaps concentrate at 2–5 am (hours 3 and 4 account for 34 each), when demand is lowest. The longest runs line up with known events: **36 h from 2012-10-29 01:00 (Sandy), 22 h from 2011-01-26 18:00 (snowstorm), 13 h from 2011-08-27 18:00 (Hurricane Irene)**. | **Working interpretation: a missing hour means zero rentals** (the source only logs hours with ≥ 1 rental). This is an inference, not documented. Reindex to the full hourly grid, and flag these hours (`imputed_zero`). Use the grid (missing = 0) when computing lag/rolling features, never row position. Fit models and score on the **observed rows** as the main result (this matches the 11,460 / 5,919 split), and report a sensitivity check with the imputed zeros included. Weather values are unavailable for these hours, so forward-fill them only where needed for features. |
| Season coding | Season 1 spans Dec–Mar (it is winter). **The PDF and the local `Readme.txt`** say 1 = spring, 2 = summer, 3 = fall, 4 = winter, which is off by one step from the observed months (1 = Dec–Mar, 2 = Mar–Jun, 3 = Jun–Sep, 4 = Sep–Dec). The **UCI web page's variables table** lists the correct coding (1 = winter … 4 = fall), which matches the data. | **Trust the data.** Use `season` as a categorical with labels 1=winter, 2=spring, 3=summer, 4=fall. State the discrepancy in the report with a month-by-season table. `season` and `month` overlap heavily, so check VIF and don't include both without justification. |
| Weather 4 is rare | Counts: cat1 = 11,413, cat2 = 4,544, cat3 = 1,419, **cat4 = 3**. | Keep it in EDA. For models, merge categories 3+4 to avoid an unstable coefficient. Justify in the report. |
| Suspect zeros | `windspeed == 0` in **12.5 %** of rows (likely missing values recorded as 0). `hum == 0` in 22 rows (a single-day sensor fault). | Flag as suspect. Test sensitivity (e.g. an indicator variable, or imputation) rather than trusting them. |
| Overdispersion | `cnt` mean ≈ 189, variance ≈ 32,901, max 977. | Variance ≫ mean, so OLS assumptions are violated. Use log-OLS and Poisson/NegBin GLMs. |
| Identity holds | `casual + registered == cnt` in all rows. | **`casual`/`registered` must never be features for `count`** (they are the target's components). |
| Trend | Mean `cnt` is 143.8 in 2011 and 234.7 in 2012 (+63 %). | Include a year/trend term. Failing to model it biases 2012 predictions. |
| Extreme events | **Correction:** the low daily totals around Hurricane Sandy are mostly *missing hours*, not observed low demand. 2012-10-29 has 1 row (22 rentals) and 2012-10-30 has 11 rows (1,096 rentals), because hours 01:00 on 10-29 to 12:00 on 10-30 are absent. Both days are weather category 3 and windspeed is high. The same pattern appears for the 2011-01-26 snowstorm and Hurricane Irene (2011-08-27). | Never compare daily totals across days without checking the row count. Keep these days but flag them, since 2012-10-29/30 and 2011-08-27 fall inside test windows. Report errors with and without the event windows. |
| Coarse measurements | `temp` has only 50 distinct values, `hum` 89, `windspeed` 30. The smallest positive windspeed is 0.0896 (×67 ≈ 6), so there is nothing between 0 and 6. Zeros are spread evenly across years (12.8 % / 12.3 %) and rise a little in autumn (15–17 % in Sep–Dec). | Treat `windspeed = 0` as "below sensor resolution or not recorded". Add a `windspeed_zero` indicator and check sensitivity. The coarse resolution is a limitation to mention. |
| Split sizes | **Verified:** day ≤ 20 gives 11,460 train rows and day ≥ 21 gives 5,919 test rows (total 17,379). There are 24 test windows of 180–264 observed rows each (a full 11-day window is 264). Train has 455–480 rows per month. | Assert these numbers in the notebook. |
| Lag availability | For the 336 h lag, 99.7 % of test hours have the lagged timestamp present in the data. The first month (2011-01) has no earlier history, so its early training rows have no 336 h lag. | Treat 2011-01 as a cold-start window (lag features are NaN for its first 14 days). Say so in the report. |
| Calendar consistency | **Verified:** no nulls or duplicates, rows are sorted, `yr`/`mnth`/`weekday` all match `dteday`, `workingday` matches weekday and holiday in every row, there are 21 holiday dates, and `casual + registered = cnt` in every row. | No cleaning needed beyond the items above. |
| Extra columns | `instant` is a row index. `yr`, `mnth` and `weekday` are redundant with `datetime`. | Drop `instant`. Derive time features from `datetime`. |

---

## 3. Notebook / report structure

1. Setup & reproducibility (seeds, library versions, `RANDOM_STATE = 42`)
2. Data loading, schema mapping, denormalization, gap handling, sanity checks
3. Task 1: EDA
4. Task 2: Regression analysis
5. Task 3: Forecasting (split, leakage design, features, models, results, error analysis)
6. Limitations and conclusions

The PDF memo follows the same order in about 4–6 pages: tables for regression and metrics, roughly 6–8 figures, and mostly interpretation.

---

## 4. Task 1: EDA (Tier 2)

**Required:**
- Data-quality summary: dtypes, missing hours, duplicates, ranges, and the suspect zeros from §2.
- Distribution of `count`, `casual` and `registered` (histogram, mean vs variance, skew).
- Hour-of-day profiles split by `workingday` (commute double-peak vs weekend midday peak).
- Day-of-week, month and season effects. Year-over-year growth.
- Weather category, temperature, humidity and windspeed vs demand.
- Casual vs registered comparison: profile shape, weekday vs weekend, share of total.
- Correlation matrix, including the `temp`–`atemp` correlation.
- Anomaly analysis: Sandy, holidays, days with missing hours, weather-4 hours.
- At least 3–5 written insights, each stating what was found and why it matters for modeling.

**Pitfalls to avoid:** plots without interpretation, treating `hr`/`month`/`weather` as continuous in visuals, ignoring the year trend, and mixing units after denormalization.

---

## 5. Task 2: Regression analysis (Tier 2)

**Design**
- Response variables: `log(count+1)` and `count`. Also `casual` and `registered` separately.
- Predictors: hour (categorical), workingday/holiday, season/month, weather (categorical, 3+4 merged), temp, humidity, windspeed, year.
- Models compared: OLS (log target) → **Poisson GLM** → **Negative Binomial GLM**. Use AIC/BIC and a pseudo-R² for comparison.

**Required diagnostics and discussion**
1. **Multicollinearity:** VIF table. `temp` and `atemp` are near-duplicates, so drop `atemp` (or use a composite), and show VIFs before and after.
2. **Non-linearity:** Add a quadratic or spline term for temperature, and an `hour × workingday` interaction. Show the improvement.
3. **Count distribution / overdispersion:** Compute the dispersion statistic. Use it to justify Negative Binomial over Poisson.
4. **Autocorrelated residuals:** ACF plot and Durbin-Watson. Report **HAC (Newey-West) standard errors** alongside the naive ones, because hourly data violates independence.
5. **Heteroscedasticity / residual plots / Q-Q plot.**
6. **Casual vs registered:** Side-by-side coefficient comparison with interpretation. Use incidence rate ratios (`exp(β)`) for the count models, e.g. "+1 °C → +x % casual vs +y % registered".
7. **Variable-selection logic:** Domain reasoning first, then AIC-based comparison, then Lasso as a robustness check. No blind stepwise selection.

**Pitfalls to avoid:** both `temp` and `atemp` in the same model; the numeric encoding of categorical variables; reading OLS p-values as trustworthy; interpreting coefficients causally; using `casual`/`registered` as predictors of `count`; forgetting that weather effects vary by user type.

---

## 6. Task 3: Forecasting (Tier 2)

### 6.1 Split (prescribed by the PDF)
- Train: days 1–20 of every month. Test: day 21 to month end. 24 evaluation windows (12 months × 2 years), each with ≤ ~264 hours.
- Print the row counts (expected 11,460 / 5,919) and assert there is no overlap.

### 6.2 Forecast origin and leakage design
- **Define the forecast origin as 00:00 on day 21 of each month.** The horizon is 1 to ~264 hours.
- **Never use `casual`/`registered`, or any same-window `count`, as a feature.**
- **Lag features must respect the horizon.** Use lags ≥ 336 h (14 days), which exist for every hour in the window, or aggregates computed only from data before the origin (e.g. hour-of-week means over the last N weeks). No 1-hour or 24-hour lags unless doing recursive forecasting, which is out of scope.
- **Rolling statistics:** compute them shifted so they never touch the test window.
- **Fit all encoders and scalers on the training data only.**
- **Weather in the test window is not known at the origin.** Report two clearly-labelled scenarios:
  - **(A) Strict:** calendar and history-derived features only.
  - **(B) Oracle weather:** adds actual weather as if perfectly forecast. This is an upper bound, and the assumption is stated in the report.
- **Chronology flaw in the prescribed split:** training on e.g. Dec 1–20 to predict Jan 21–31 uses data from the "future" of some test windows. Use the prescribed split as the **main result**, and add a **rolling-origin (expanding-window) backtest** where each window is predicted using only earlier data. Report the gap between the two.

### 6.3 Features
Hour, day of week, month, year / time index (trend), holiday, workingday, rush-hour flag, cyclical sin/cos for hour and month, and lagged/hour-of-week aggregates (≥ 336 h). Scenario B adds temp, humidity, windspeed, weather.

### 6.4 Models (compare ≥ 4)
1. Seasonal-naive baseline ("same hour, 1–2 weeks earlier", or a hour × workingday historical mean).
2. NegBin/Poisson GLM.
3. Random forest.
4. Gradient boosting (LightGBM/XGBoost) with a Poisson objective or log target.

Optional: SARIMAX/Prophet if time permits.

### 6.4a Training setup
- Hyperparameters are tuned with **time-blocked CV inside the training set only**. The test set is evaluated once.
- Predictions are clipped at 0 (or a log/Poisson objective is used).
- Fixed random seeds.

### 6.5 Evaluation
- **Metrics:** RMSLE (primary, because it handles skew and low counts), MAE, RMSE. Avoid plain MAPE (unstable near 0), and if sMAPE is included, say why.
- **Breakdowns:** per window (24 windows, table or heatmap), by hour of day, by workingday vs weekend, and the Sandy window separately.
- **Error analysis:** the worst windows/hours and why (weather extremes, holidays, trend).
- **Interpretability:** permutation importance or SHAP for the best model.
- **Visuals:** actual vs predicted for representative windows (best, typical, worst).
- **Optional:** prediction intervals.

**Pitfalls to avoid:** shuffled splits; tuning on the test set; preprocessing fit on the full data; leakage through lags/rolling means; reporting a single aggregate number; comparing models without a baseline; negative predictions; ignoring the 2012 level shift.

---

## 7. Master pitfalls checklist

**Data**
- [ ] Denormalized the weather variables
- [ ] Checked `season` coding against the month
- [ ] Reindexed to the full hourly grid, and gaps documented
- [ ] Investigated windspeed = 0, hum = 0, weather 4, and the Sandy/Irene/snowstorm gaps (check row counts before reading daily totals)
- [ ] Missing-hour = zero-rental assumption stated and tested with a sensitivity check
- [ ] Dropped `instant`

**Regression**
- [ ] `temp`/`atemp` collinearity resolved (VIF shown)
- [ ] Categoricals one-hot encoded
- [ ] Overdispersion tested and NegBin justified
- [ ] Non-linearity and interactions handled
- [ ] Autocorrelation addressed (HAC SEs)
- [ ] `casual`/`registered` not used to predict `count`
- [ ] Casual vs registered compared and interpreted

**Forecasting**
- [ ] Exact prescribed split, sizes printed
- [ ] Forecast origin defined, and lags ≥ horizon
- [ ] Scenario A vs B labelled
- [ ] Preprocessing fit on train only
- [ ] Baseline included
- [ ] Tuning inside training only
- [ ] Per-window and per-hour results
- [ ] Rolling-origin backtest included
- [ ] Predictions clipped ≥ 0

**Submission**
- [ ] Notebook runs top to bottom from a fresh kernel
- [ ] Seeds and library versions recorded
- [ ] The report interprets results and states limitations
- [ ] Figures have labelled axes and units

---

## 8. Stretch goals (only if time permits)

SARIMAX/Prophet comparison; separate casual and registered forecasts summed vs direct `count`; conformal prediction intervals; level × shape decomposition.

---

## 9. Schedule (Sept 20–25, shared with Part 2)

| Day | Work |
|---|---|
| Sept 20 | Data prep, EDA |
| Sept 21 | Regression (OLS → GLM, diagnostics, casual vs registered) |
| Sept 22 | Forecasting: split, features, baselines, first GBM |
| Sept 23 | Rolling-origin check, per-window/error analysis. Start Part 2 in parallel, since it needs GPU time. |
| Sept 24–25 | Report writing, notebook cleanup, final fresh-kernel run |

---

## 10. Decision log

| Date | Decision |
|---|---|
| 2026-09-20 | Use UCI `hour.csv` (professor's suggested dataset) only. |
| 2026-09-20 | Target Tier 2 quality. |
| 2026-09-20 | Denormalize weather variables, reindex to the hourly grid, merge weather 3+4 for modeling. |
| 2026-09-20 | Forecast origin is 00:00 on day 21. Lags ≥ 336 h. Two weather scenarios (A strict / B oracle). |
| 2026-09-20 | Prescribed split is the main result. Rolling-origin backtest is the robustness check. |
| 2026-09-20 | Primary metric is RMSLE, with MAE and RMSE as secondary. |
| 2026-09-21 | Season labels follow the observed data (1=winter … 4=fall), not the PDF/Readme coding. This matches the UCI web page. The discrepancy is documented in the report. |
| 2026-09-21 | Denormalization uses the UCI web page's formulas: min-max for temp/atemp (−8…39, −16…50), ×100 for humidity, ×67 for windspeed. The local Readme's ÷41/÷50 is not used. |
| 2026-09-21 | Missing hours are interpreted as zero rentals (no `cnt = 0` rows exist, gaps sit at night and during storms). Main results use observed rows. Imputed zeros are used for lag computation and a sensitivity check. Sandy/Irene/snowstorm windows are flagged and reported separately. |
| 2026-09-21 | Environment: `.venv/` in the project root (Python 3.14, pandas, statsmodels, scikit-learn, lightgbm, matplotlib, seaborn, jupyter). |
| 2026-09-21 | Task 2: joint-MLE Negative Binomial (`smf.negativebinomial`) failed to converge on the full regression design (too many sparse dummy cells, NaN standard errors). Switched to the Cameron-Trivedi two-step NB2 estimator (Poisson → auxiliary OLS for alpha → GLM-NB with fixed alpha) for both the main model and the casual/registered comparison. |
| 2026-09-21 | Task 3: history-derived features use `lag_336` (2-week lag), `hw_avg_4to7w` (mean of 2/3/4/5-week lags, skipna) and `how_expanding_mean` (expanding same-hour-of-week mean of `lag_336`). Raw `lag_504`/`lag_672`/`lag_840` are not used as standalone features because they are `NaN` for part of the 2011-01 test window (cold start); the skipna-averaged/expanding features have zero `NaN` in any test row. Minimum safe lag is 264h (the longest window); 336h is used for margin. |
| 2026-09-21 | Task 3: LightGBM's CV search (Poisson objective, trained on raw `count`) must be scored with an explicit RMSLE scorer, not `neg_root_mean_squared_error` on raw counts, the two are not equivalent for this target and using RMSE-on-raw-counts silently selected an undertrained model (test RMSLE 0.688, worse than the naive baseline) that looked fine on CV RMSE. The Random Forest search is unaffected because it is trained on `log1p(count)`, where RMSE and RMSLE coincide exactly. |

*Append new decisions to this table as they are made.*
