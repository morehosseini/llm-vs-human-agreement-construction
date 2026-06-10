# Evaluating the Agreement Between Large Language Models and Human Reviewers in Classifying Construction Research

This repository contains the replication code, datasets, figures, and appendices for the paper:
**"Evaluating the Agreement Between Large Language Models and Human Reviewers in Classifying Construction Research: A Quantitative Agreement Study"**.

This research was conducted within the **Faculty of Architecture, Building and Planning, University of Melbourne**.

---

## Study Overview

The adoption of artificial intelligence (AI) and machine learning (ML) within the construction domain has led to a rapid expansion of academic literature. Systematic reviews are essential for synthesising this knowledge, but manual screening and categorisation of large document corpora are labor-intensive. 

This study evaluates the chance-corrected agreement between four state-of-the-art Large Language Models (LLMs) and trained human reviewers in categorising 1,804 construction research abstracts using a six-class taxonomy.

### Key Contributions
1. **Chance-Corrected Human–AI Agreement Evaluation:** Benchmarking four models (GPT-5 Full, GPT-5 mini, Gemini Pro, and Gemini 2.5 Flash) against a consensus human benchmark using Cohen's kappa ($\kappa$), Gwet's AC1, and Macro-F1.
2. **Multi-Layered Reasoning Alignment Analysis:** Assessing the semantic alignment of model-generated rationales against formal codebook definitions using lexical TF–IDF cosine similarity.
3. **Practical Guidance for Human-in-the-Loop Triage:** Developing evidence-based routing thresholds that auto-accept high-confidence model predictions and redirect low-confidence ones to human adjudicators to minimise manual workload.

---

## Repository Structure

```
.
├── README.md               # Study overview and replication guide (Australian English)
├── APPENDICES.md           # Verbatim System Prompt (Appendix A) and JSON Schema (Appendix B)
├── LICENSE                 # MIT License
├── .gitignore              # Standard Python gitignore rules
├── data/
│   ├── unified_labels.csv  # The final unified dataset (1,804 records)
│   ├── result_GPT5_Full.csv # Raw model classifications: GPT-5 Full
│   ├── result_gpt_5_mini.csv # Raw model classifications: GPT-5 mini
│   ├── result_Geminipro.csv  # Raw model classifications: Gemini Pro (1–10 confidence scale)
│   ├── result_gemini_2.5_flash.csv # Raw model classifications: Gemini 2.5 Flash
│   ├── human_labels_s.csv  # Anonymised human classifications: Agent S
│   ├── human_labels_r.csv  # Anonymised human classifications: Agent R (includes reasons)
│   ├── human_labels_m.csv  # Anonymised human classifications: Agent M
│   ├── results.json        # Unified evaluation metrics output by scripts
│   ├── human_reliability_and_coverage.json # Reliability and coverage metrics output by scripts
│   └── pairwise_kappa.csv  # Model-to-model and human-to-model kappa matrix
├── figures/                # Main manuscript figures
│   ├── Figure_01_Cohen_s_kappa_heatmap_across_humans_and_AI_models.png
│   ├── Figure_02_AI_agents_similarity_to_humans_kappa.png
│   ├── Figure_03_Confidence_vs_human_agreement_tier_best_model.png
│   ├── Figure_04_Confusion_matrix_best_model_vs_HighConf_human_consensus.png
│   ├── Figure_05_Hierarchical_clustering_dendrogram_of_the_four_AI_agents_against_the_HighConf_hu.png
│   ├── Figure_06_Definition_consistency_by_model_ArgmaxMatch_rate.png
│   ├── Figure_07_Distribution_of_assigned_definition_similarity_by_model_boxplot.png
│   ├── Figure_08_Distribution_of_specificity_margin_by_model_boxplot.png
│   ├── Figure_09_Mean_rationale_definition_alignment_by_model_and_class_heatmap_mean_cosine_simil.png
│   ├── Figure_10_Class_wise_mean_assigned_definition_similarity_grouped_bars.png
│   ├── Figure_11_Class_wise_definition_consistency_ArgmaxMatch_rate_grouped_bars.png
│   ├── Figure_12_Class_wise_specificity_margin_s_assigned_s_alt_grouped_bars.png
│   └── Figure_13_Model_to_model_semantic_similarity_of_rationales_centroid_cosine_heatmap.png
└── scripts/
    ├── analysis.py         # Main analysis and metrics pipeline
    └── human_reliability_and_coverage.py # Human reliability & confidence-coverage metrics
```

---

## Replication Guide

### Prerequisites & Dependencies

The replication scripts require Python 3.11+ and the following libraries:
- `pandas` (>= 2.0.0)
- `numpy` (>= 1.24.0)
- `matplotlib` (>= 3.7.0)
- `scipy` (>= 1.10.0)

You can install the dependencies via `pip`:
```bash
pip install pandas numpy matplotlib scipy
```

### Running the Analysis

To run the primary replication pipeline and recompute all agreement tables and statistical values:
```bash
python scripts/analysis.py
```
This script will:
- Align and merge raw human annotations and AI predictions.
- Calculate the majority-vote consensus benchmark.
- Recompute Table 3 (HighConf metrics) and Table 4 (MedConf metrics) with 95% bootstrapped confidence intervals.
- Save the unified dataset to `data/unified_labels.csv`.
- Save the metrics output to `data/results.json`.
- Export `figures/figure13_calibration.png` and `figures/figure14_dendrogram.png`.

To recompute human annotator reliability (Cohen's and Fleiss' kappa) and confidence-ranked triage coverage metrics:
```bash
python scripts/human_reliability_and_coverage.py
```
This script will:
- Recompute human inter-rater reliability on the triple-labelled subset.
- Compute model-wise precision at confidence-ranked coverage levels (10%, 25%, 50%, 75%, 100%) on the HighConf subset.
- Save the metrics to `data/human_reliability_and_coverage.json`.

---

## Anonymisation and Ethics Statement

To comply with double-blind peer-review guidelines and project ethics protocols, the human annotators' real identities have been anonymised in all public-facing datasets, figures, and scripts. They are referenced throughout as **Agent S**, **Agent R**, and **Agent M** (or initials `S`, `R`, and `M`). All local directory paths have been stripped.

---

## Citation

If you use this repository or dataset in your work, please cite the main paper:

**APA 7th Edition:**
> Hosseini, M. R., et al. (2026). Evaluating the Agreement Between Large Language Models and Human Reviewers in Classifying Construction Research: A Quantitative Agreement Study. *Faculty of Architecture, Building and Planning, University of Melbourne*. https://github.com/morehosseini/llm-vs-human-agreement-construction

---

## References

- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174. https://doi.org/10.2307/2529310
- Feinstein, A. R., & Cicchetti, D. V. (1990). High agreement but low kappa: I. The problems of two paradoxes. *Journal of Clinical Epidemiology*, 43(6), 543–549. https://doi.org/10.1016/0895-4356(90)90158-L
- Gwet, K. L. (2008). Computing inter-rater reliability and its variance in the presence of high agreement. *British Journal of Mathematical and Statistical Psychology*, 61(1), 29–48. https://doi.org/10.1348/000711006X115907
- Dai, Z.-Y., et al. (2025). Screening academic literature using large language models: A comparison of zero-shot and few-shot paradigms. *Journal of Medical Internet Research*, 27, e67488. https://doi.org/10.2196/67488
- Törnberg, P. (2024). How to use LLMs for text analysis: An assessment of ground-truth crisis and best practices. *Sociologica*, 18(1), 35–62. https://doi.org/10.6092/issn.1971-8853/18413
- Törnberg, P. (2023). ChatGPT-4 outperforms crowd workers and experts in annotating political text. *arXiv preprint arXiv:2304.06588*. https://doi.org/10.48550/arXiv.2304.06588
- Matsui, T., et al. (2024). Accuracy of large language models in screening citations for systematic reviews of bipolar disorder. *JMIR Mental Health*, 26, e52758. https://doi.org/10.2196/52758
