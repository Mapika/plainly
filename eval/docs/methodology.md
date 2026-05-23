# Evaluating "plainly": A Defensible Statistical Methodology for Measuring How Well Style-Smell Scores Separate Human from AI Prose

**Scope.** You have a labeled corpus (human-written vs AI-generated) across registers including scientific/academic writing, and a tool ("plainly") that emits a per-document continuous **density** score plus auxiliary metrics (sentence-length CoV, overused-word rates, etc.). The question is: *how well do these scores separate the two classes, defensibly and grounded in the literature?* This report gives (A) the methodology with pure-stdlib formulas, and (B) the supporting literature.

A note on framing before any math: **your scores are a *detector*, and the field that knows how to evaluate detectors rigorously is the AI-text-detection literature** (RAID, Binoculars, DetectGPT). The single most important lesson from that literature — repeated below — is that **accuracy and overall AUROC are misleading; the operating metric that matters for a writing tool is the false-positive rate (flagging human text as AI) at a fixed, low threshold.** Build the whole evaluation around that.

---

## Part A — Methodology

### 0. Setup and conventions

Let the metric of interest (e.g. density) produce values for the two groups:

- Human group: `H = [h_1, ..., h_{n1}]` (n1 values). Treat **human as the "positive-for-FPR" reference class** (the class you must not falsely flag).
- AI group: `A = [a_1, ..., a_{n2}]` (n2 values).

For detection framing, define the **positive class = AI** (the thing the detector is supposed to catch) and assume **higher density ⇒ more AI-like** (verify the sign empirically; if AI scores lower, flip the score). Be explicit and consistent about sign — half the bugs in these evaluations are sign errors.

All formulas below are implementable with `math` and `random` from the standard library only.

---

### 1. Distribution comparison: is the metric different between human and AI?

You want both a **nonparametric** test (robust, no normality assumption — the right default for skewed style metrics) and a **parametric** one (Welch's t, for completeness and because reviewers expect it).

#### 1a. Mann–Whitney U (Wilcoxon rank-sum) with normal approximation

This tests whether one group tends to produce larger values than the other. It is the rank-based workhorse and — critically — it is **algebraically identical to ROC AUC** (see §3), so it does double duty.

**Procedure:**

1. Pool all `N = n1 + n2` values and assign ranks 1..N (smallest = 1). **Handle ties by averaging ranks** (assign each member of a tie group the mean of the ranks they span). This matters: style metrics produce many ties.
2. Let `R1` = sum of ranks of the human group.
3. Compute the U statistics:

```
U1 = R1 - n1*(n1 + 1)/2
U2 = n1*n2 - U1
U  = min(U1, U2)        # for a two-sided test
```

4. Under H0 the mean and (tie-corrected) variance of U are:

```
mu_U  = n1*n2 / 2

# tie correction: for each group of tied values of size t_j,
# let  sum_t = sum_j (t_j^3 - t_j)
var_U = (n1*n2 / 12) * ( (N + 1) - sum_t / (N*(N - 1)) )
```

(If there are no ties, `sum_t = 0` and this reduces to `n1*n2*(N+1)/12`.)

5. **z with continuity correction** (subtract 0.5 toward the mean):

```
z = (U - mu_U + 0.5*sign(mu_U - U)) / sqrt(var_U)
# equivalently: numerator = |U - mu_U| - 0.5, then z = -numerator/sqrt(var_U)
```

6. Two-sided p-value from the standard normal CDF Φ:

```
p = 2 * (1 - Phi(|z|))
```

with the error-function-based normal CDF (stdlib `math.erf`):

```
Phi(x) = 0.5 * (1 + erf(x / sqrt(2)))
```

**Caveat:** the normal approximation is fine for n1, n2 ≳ 20 each. For tiny strata, note the p-value is approximate and consider reporting the effect size (§2) as primary instead.

#### 1b. Welch's t-test (unequal variances)

Do **not** use Student's pooled-variance t-test — the two classes rarely have equal variance (AI text is typically *less* variable). Welch is the correct default.

```
mean_H, mean_A           # sample means
s2_H, s2_A               # sample variances (divide by n-1, the unbiased estimator)

t = (mean_H - mean_A) / sqrt(s2_H/n1 + s2_A/n2)

# Welch–Satterthwaite degrees of freedom:
df = (s2_H/n1 + s2_A/n2)^2
     / ( (s2_H/n1)^2/(n1-1) + (s2_A/n2)^2/(n2-1) )
```

p-value needs the Student-t CDF. Without scipy, use the regularized incomplete beta function `I_x(a,b)`, which is implementable in stdlib via a continued fraction (Lentz's algorithm). For two-sided:

```
x   = df / (df + t*t)
p   = I_x(df/2, 1/2)     # this is the two-sided p-value directly
```

`I_x(a,b)` = `betacf`-based continued fraction times `exp(a*ln(x) + b*ln(1-x) - lnBeta(a,b)) / a`, with `lnBeta(a,b) = lgamma(a)+lgamma(b)-lgamma(a+b)` (all from `math`). This is ~30 lines of code; it's the standard Numerical-Recipes `betai` routine. If you prefer to avoid it, report the t-statistic and df and rely on the Mann–Whitney p-value as your headline test (recommended anyway, since the metric is non-normal).

**Reporting rule:** lead with Mann–Whitney (assumption-light) and report Welch's t alongside. If they disagree, that disagreement is itself informative (usually means heavy skew or outliers — investigate, don't paper over).

---

### 2. Effect size — report this, not just p-values

p-values conflate effect magnitude with sample size; with thousands of documents everything is "significant." Effect size is what tells you whether the separation is *practically* useful.

#### 2a. Cliff's delta (δ) — the nonparametric effect size, and it's an AUC in disguise

δ is the probability that a random AI document scores higher than a random human one, minus the reverse:

```
delta = ( #(a > h) - #(a < h) ) / (n1*n2)      over all pairs (a in A, h in H)
```

Range −1..+1; 0 = complete overlap. **Direct relation to AUC:**

```
AUC = (delta + 1) / 2          # so delta = 2*AUC - 1
```

This is the cleanest link in the whole report: the rank-sum U, Cliff's δ, and ROC AUC are three views of the same quantity.

**Interpretation thresholds (Romano et al. 2006, the standard cite):**

| |δ|          | magnitude   | equivalent AUC |
|--------------|-------------|----------------|
| < 0.147      | negligible  | < 0.574        |
| 0.147–0.33   | small       | 0.574–0.665    |
| 0.33–0.474   | medium      | 0.665–0.737    |
| ≥ 0.474      | large       | ≥ 0.737        |

#### 2b. Rank-biserial correlation

Equivalent reparameterization of the same information, often reported with Mann–Whitney:

```
r_rb = 1 - 2*U1/(n1*n2)        # = -delta with the sign convention above; |r_rb| = |delta|
```

Report whichever your audience expects; they carry identical information.

#### 2c. Cohen's d (parametric effect size)

For the t-test framing. Use the **pooled SD** version, but since variances differ, also report Glass's Δ or just be explicit:

```
s_pooled = sqrt( ((n1-1)*s2_H + (n2-1)*s2_A) / (n1+n2-2) )
d = (mean_A - mean_H) / s_pooled
```

Thresholds (Cohen): 0.2 small, 0.5 medium, 0.8 large. Treat d as secondary to δ for skewed metrics.

---

### 3. Classification performance: treat the score as a detector

This is the heart of the evaluation. The score is a continuous detector; sweeping a threshold over it traces an ROC curve.

#### 3a. ROC AUC from ranks (no curve-fitting needed)

Because of the rank-sum identity, you get AUC essentially for free and exactly:

```
AUC = U_AI / (n1*n2)
```

where `U_AI` is the U statistic computed with **AI as the positive class** (i.e. `U_AI = R_AI - n2*(n2+1)/2` using AI's rank sum, then AUC = U_AI/(n1*n2)). **Ties contribute 0.5 each** — the averaged-ranks procedure in §1a handles this automatically, which is why the rank formula is preferred over a naive threshold sweep. AUC = 0.5 is chance; 1.0 is perfect separation.

Interpretation: AUC is the probability that a randomly chosen AI document is ranked above a randomly chosen human document. **It is threshold-independent and prevalence-independent** — which is its strength (a clean summary of separability) and its weakness (it hides what happens at the low-FPR operating point you actually care about).

#### 3b. Precision–Recall curve and AUPRC

Under class imbalance (e.g. mostly human text in the wild), PR curves are more informative than ROC. To build one, sort all documents by score descending; sweep the threshold through each unique score; at each threshold:

```
TP = AI docs at or above threshold
FP = human docs at or above threshold
FN = AI docs below threshold

precision = TP / (TP + FP)
recall    = TP / (TP + FN)        # = TPR
```

Plot precision (y) vs recall (x). **AUPRC** via the trapezoidal rule over the points, or the more honest *average precision*:

```
AP = sum over thresholds k of (recall_k - recall_{k-1}) * precision_k
```

Baseline AUPRC = prevalence of the positive class (unlike ROC's fixed 0.5 baseline), so always report the prevalence next to AUPRC.

#### 3c. Choosing and reporting an operating threshold

Do **not** report only AUC. Pick a threshold and report the confusion matrix at it. Three defensible ways to choose:

1. **Fixed FPR (recommended, this is the RAID/Binoculars standard).** Calibrate the threshold *on human data only* so that FPR = a fixed target (1% or 5%). Report **TPR at that FPR** (often written TPR@1%FPR, TPR@5%FPR). This is the field-standard headline number.
2. **Youden's J:** threshold maximizing `TPR - FPR`. Statistically tidy but ignores the asymmetric cost of false accusations — use only as a secondary reference point.
3. **Fixed high-precision point:** threshold giving e.g. 99% precision, report the recall there.

#### 3d. False-positive rate at a fixed threshold — and why FPR is *the* metric for a writing tool

```
FPR = (# human documents flagged as AI) / (total human documents)
```

For a tool that scores *people's writing*, a false positive is a human author wrongly told their prose is AI-like — a reputational/accusatory harm. The cost is **highly asymmetric**: missing some AI text (a false negative) is mild; falsely flagging a human is severe. Therefore:

- **Accuracy is the wrong headline metric** — it weights both error types equally and is dominated by whatever class is more prevalent.
- **Report TPR (detection rate) at a fixed low FPR (1%, 0.1% if data allow).** RAID and Binoculars both adopt exactly this paradigm precisely because false positives are the operationally dangerous error. Binoculars famously reports >90% detection at 0.01% FPR; RAID calibrates every detector to a fixed 5% FPR before comparing.
- State the threshold explicitly and the FPR it was calibrated to, so the number is reproducible.

---

### 4. Confidence intervals via bootstrap (percentile method)

A point estimate of AUC or FPR without an interval is not defensible. Use the nonparametric **percentile bootstrap** (stratified by class so group sizes stay fixed).

**Procedure (for any statistic θ — AUC, FPR@threshold, TPR@FPR, Cliff's δ):**

```
for b in 1..B:                       # B = 2000 to 10000
    H* = sample n1 values from H WITH replacement
    A* = sample n2 values from A WITH replacement
    theta_b = compute_statistic(H*, A*)
collect theta_1 ... theta_B (sorted)

95% percentile CI = [ 2.5th percentile, 97.5th percentile ] of the theta_b
```

In stdlib: `random.choices(H, k=n1)` for resampling; sort the `theta_b` list and index at `int(0.025*B)` and `int(0.975*B)`.

**Notes / caveats:**
- **Stratify** (resample within each class) so n1, n2 are preserved each iteration — important for FPR, which is a property of the human class alone.
- For **FPR at a fixed threshold**, the threshold should ideally be re-derived inside each bootstrap iteration if it was data-calibrated, otherwise the CI is optimistically narrow. If you fix the threshold from the full data and only bootstrap the FPR estimate, say so.
- The percentile bootstrap is known to **undercover slightly** for AUC (see the pROC/DeLong literature). For a more accurate interval use **BCa** (bias-corrected and accelerated) — more code but still pure stdlib. For AUC specifically, **DeLong's analytic variance** is the gold standard in the diagnostic literature; if you implement only one analytic CI, do AUC via DeLong and bootstrap everything else. Be honest about which you used.
- If documents are **clustered** (multiple texts per author/journal), the naive bootstrap is invalid — resample *clusters*, not documents, or your CIs will be far too narrow.

---

### 5. Stratification by register/domain (general vs scientific)

**Report per-stratum, never only pooled.** Reasons:

- **Simpson's paradox / confounding:** scientific prose is denser, more nominal, and lower-burstiness *even when human-written*. If the human set skews general-register and the AI set skews scientific (or vice versa), a pooled AUC can look excellent while measuring register, not authorship. Per-stratum AUC controls for this.
- **Operationally, the tool is used within a register.** A scientist cares about FPR *on scientific human writing specifically* — which is exactly the population most likely to be falsely flagged, because formal academic style overlaps with LLM style (Kobak et al.; the Liang non-native-speaker bias result is the canonical warning).

**Procedure:** compute every §1–§4 statistic separately within {general, scientific} (and finer if you have it). Then optionally a pooled estimate **with the stratum as a covariate** acknowledged.

**Multiple-comparisons caveat.** If you run k strata × m metrics tests, you inflate false positives. Adjust:

- **Bonferroni:** reject if `p_i < alpha/k`. Simple, conservative.
- **Holm–Bonferroni (preferred — uniformly more powerful, same assumptions):** sort p-values ascending `p_(1) ≤ ... ≤ p_(k)`; reject `p_(i)` while `p_(i) < alpha/(k - i + 1)`; stop at the first failure and retain all the rest.

Apply correction to the *family* of hypothesis tests; effect sizes and AUCs with CIs don't need it (CIs already convey uncertainty), but be consistent about what family you're controlling.

---

### 6. Pitfalls (read this section twice)

1. **Class imbalance.** Real-world prevalence of AI text is unknown and usually low. ROC AUC is prevalence-invariant (good for separability) but precision and PPV are *not* — a detector with 99% specificity still produces mostly false alarms if AI prevalence is 1%. Report AUPRC + prevalence, and if you claim real-world precision, state the assumed base rate.

2. **Dataset contamination / construction artifacts.** If "human" texts and "AI" texts differ in topic, length, formatting, source corpus, or era, the classifier learns the artifact, not the tell. The Desaire-style pipelines control this by generating AI versions *of the same human passages*. Match topic and source as tightly as you can; otherwise your AUC is an upper bound that won't survive contact with reality.

3. **Length confounds.** Many style metrics (vocabulary richness, burstiness, sentence-length CoV) are length-dependent. If AI and human texts differ in word count, you may be measuring length. **Controls:** (a) report word-count distributions per class and test them (Mann–Whitney on length); (b) truncate/bin to comparable lengths; (c) regress the metric on log(word count) and analyze residuals; (d) stratify by length band as in §5. At minimum, demonstrate that the separation survives length-matching.

4. **The "decline effect" / human–LLM coevolution.** Tells are *non-stationary*. Once "delve" and "underscore" were publicized in early 2024, their frequency dropped sharply (the arXiv/PubMed "delve" decline; Human–LLM Coevolution work). Authors edit LLM output, and models change. Consequences: (a) a tool tuned to 2023 tells degrades over time; (b) **always report the date/version of the AI generations in your corpus**; (c) treat any single-snapshot AUC as time-stamped, not permanent; (d) re-evaluate periodically.

5. **High AUC ≠ real-world accuracy.** This is the central skeptical point and the RAID finding in one line: detectors that look near-perfect on a benchmark **"suddenly deteriorate from perfect accuracy to total failure"** under domain shift, paraphrase, or adversarial editing, and show clear bias toward domains/models they were tuned on. A high AUC on *your* labeled corpus demonstrates separability *on that corpus's distribution* — nothing more. To make claims travel: hold out unseen models, unseen domains, and lightly-edited/paraphrased AI text; report degradation, not just the best number. And remember the Liang et al. (Patterns 2023) result — perplexity-style signals falsely flagged **61%** of non-native-English human essays. A "style smell" tool is at acute risk of the same bias; test it explicitly on non-native and on formal-scientific human writing, because those are the humans it will wrongly accuse.

**Headline recommendation.** Lead your report with: per-stratum **AUC (with bootstrap CI)** + **TPR at 1% FPR (with CI)** + **Cliff's δ** + a length-confound check, dated to your generation snapshot. Relegate accuracy and pooled p-values to a footnote.

---

## Part B — Literature

### LLM tells in general and scientific/academic writing

- **Kobak, Gonzalez-Marquez, Bartoš, Hartung, Horvát — "Delving into LLM-assisted writing in biomedical publications through excess vocabulary"** (arXiv 2406.07016; published *Science Advances*, 2025; PubMed 40601754). Excess-word analysis over 14M+ PubMed abstracts (2010–2024). Estimates ≥13.5% of 2024 abstracts were LLM-processed (up to ~40% in some subfields). Identifies ~280 style "marker" words with elevated frequency (*delve, underscore, intricate, …*). This is the canonical large-scale evidence for measurable lexical tells in *scientific* writing. https://arxiv.org/abs/2406.07016 · https://www.science.org/doi/10.1126/sciadv.adt3813 · https://pubmed.ncbi.nlm.nih.gov/40601754/

- **Liang et al. — "Monitoring AI-Modified Content at Scale: A Case Study on the Impact of ChatGPT on AI Conference Peer Reviews"** (arXiv 2403.07183; ICML 2024). Corpus-level maximum-likelihood estimation of the *fraction* of LLM-modified text using reference human/AI distributions; estimates 6.5–16.9% of AI-conference peer reviews were substantially LLM-modified. Important methodological alternative: distributional estimation rather than per-document classification. https://arxiv.org/abs/2403.07183 · https://proceedings.mlr.press/v235/liang24b.html

- **Gray — "ChatGPT 'contamination': estimating the prevalence of LLMs in the scholarly literature"** (arXiv 2403.16887, 2024). Marker-word approach (e.g. ~2× rise in *intricate*, *meticulously* in 2023); a foundational, simpler precursor to Kobak et al. (Note: I cite the standard arXiv ID for Gray 2024; verify the exact identifier against your reference manager.) https://arxiv.org/abs/2403.16887

- **Desaire et al. — "Accurately detecting AI text when ChatGPT is told to write like a chemist"** (*Cell Reports Physical Science*, 2023; open copy at KU ScholarWorks). 20 hand-crafted **stylometric features** (sentence-length variability, punctuation, function-word frequencies, etc.) + XGBoost on chemistry-journal intros; 94% of human and 98–100% of AI text correctly classified, robust to obfuscation prompts. Directly relevant: this is essentially the "plainly" feature family, validated in the academic register. https://www.cell.com/cell-reports-physical-science/fulltext/S2666-3864(23)00501-5 · https://pmc.ncbi.nlm.nih.gov/articles/PMC10704924/
  - Same group, **"Almost Nobody Is Using ChatGPT to Write Academic Science Papers (Yet)"** (*MDPI Big Data Cogn. Comput.* 2024) — applies the detector at scale; useful prevalence/skeptical counterpoint. https://www.mdpi.com/2504-2289/8/10/133

- **Opara — "StyloAI: Distinguishing AI-Generated Content with Stylometric Analysis"** (arXiv 2405.10129; AIED 2024). 31 stylometric features (lexical diversity, readability, NER, sentiment) + Random Forest; 81% (AuTextification) and 98% (Education) accuracy. The closest published analogue to a "style-smell" feature vector. https://arxiv.org/abs/2405.10129

- **"Human-LLM Coevolution: Evidence from Academic Writing"** (arXiv 2502.09606, 2025). Documents the **decline effect**: marker words like *delve* dropped sharply after being publicized; evidence that authors select/edit LLM output. Cite this for Pitfall #4 (non-stationarity). https://arxiv.org/abs/2502.09606

### Perplexity/burstiness and zero-shot detection methods

- **Mitchell et al. — "DetectGPT: Zero-Shot Machine-Generated Text Detection using Probability Curvature"** (arXiv 2301.11305; ICML 2023). Curvature of model log-prob under perturbation; raises GPT-NeoX fake-news detection from 0.81 to 0.95 AUROC vs prior zero-shot baselines. **Reports AUROC as the primary metric** — representative of standard eval practice. https://arxiv.org/abs/2301.11305
  - **Fast-DetectGPT** (arXiv 2310.05130) — efficient successor via conditional probability curvature. https://arxiv.org/abs/2310.05130

- **Hans et al. — "Spotting LLMs With Binoculars: Zero-Shot Detection of Machine-Generated Text"** (arXiv 2401.12070, 2024). Perplexity / cross-perplexity ratio using two related LLMs; **>90% detection at 0.01% FPR** without training. The clearest demonstration of the **TPR@very-low-FPR** evaluation paradigm — your §3d/§4 model. https://arxiv.org/abs/2401.12070

- **GPTZero — perplexity & burstiness** (vendor documentation). Defines **burstiness** as variation in per-sentence perplexity across a document — the conceptual cousin of your sentence-length CoV / "low burstiness" smell. Useful for definitions; treat vendor accuracy claims skeptically. https://gptzero.me/news/perplexity-and-burstiness-what-is-it/

### Standard evaluation practice and robustness (what metrics detection papers report)

- **Dugan et al. — "RAID: A Shared Benchmark for Robust Evaluation of Machine-Generated Text Detectors"** (arXiv 2405.07940; ACL 2024). 6M+ generations, 11 models, 8 domains, 11 adversarial attacks. **Calibrates every detector to a fixed 5% FPR before comparing**, and finds detectors "suddenly deteriorate from perfect accuracy to total failure" under shift, with strong train-domain bias. The single best citation for your Pitfall #6 and your fixed-FPR methodology. https://arxiv.org/abs/2405.07940 · https://aclanthology.org/2024.acl-long.674.pdf

- **Liang, Yuksekgonul, Mao, Wu, Zou — "GPT detectors are biased against non-native English writers"** (*Patterns*, 2023; arXiv 2304.02819). Seven detectors misclassified **~61%** of TOEFL (non-native human) essays as AI. The definitive false-positive-harm / fairness warning — directly transferable to a perplexity/style-based tool. https://arxiv.org/abs/2304.02819

### Statistical-methods references (for the formulas)

- **Romano et al. (2006)** — the standard source for **Cliff's δ interpretation thresholds** (negligible <0.147, small <0.33, medium <0.474, large ≥0.474). Widely implemented in the R `effsize` package. https://cran.r-project.org/web/packages/effsize/effsize.pdf
- **DeLong, DeLong & Clarke-Pearson (1988)** — analytic variance for ROC AUC; gold standard for AUC CIs (vs the slightly-undercovering percentile bootstrap). Implemented in R `pROC::ci.auc`. https://search.r-project.org/CRAN/refmans/pROC/html/ci.auc.html
- Mann–Whitney U / Wilcoxon rank-sum, Welch's t, and the rank-sum↔AUC identity are textbook (Hollander & Wolfe, *Nonparametric Statistical Methods*; Hanley & McNeil 1982 for U/(n1·n2) = AUC).

### Where methods disagree (be skeptical)

- **Per-document classification (Desaire, StyloAI, DetectGPT) vs corpus-level estimation (Liang, Kobak).** The former asks "is *this* document AI?"; the latter asks "what *fraction* of this corpus is AI-influenced?" The latter is more robust precisely because per-document detection is unreliable. If your goal is auditing a corpus, prefer the distributional framing; if it's flagging individual documents, you inherit all the FPR risks above.
- **Vendor accuracy claims (GPTZero, Turnitin, Originality.ai) vs independent benchmarks (RAID, Liang Patterns).** Independent evaluations consistently report worse real-world performance and material false-positive rates, especially on non-native and formal-academic human text. Trust calibrated, fixed-FPR, multi-domain benchmarks over single-number accuracy claims — including your own.
