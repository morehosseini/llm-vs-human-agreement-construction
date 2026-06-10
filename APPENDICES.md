# Appendices

This document contains the verbatim system prompt and output JSON schema used in the paper: **"Evaluating the Agreement Between Large Language Models and Human Reviewers in Classifying Construction Research: A Quantitative Agreement Study"**.

---

## Appendix A — System Prompt (Verbatim)

The verbatim system prompt issued to all four agents is reproduced below. Decision rules and category definitions follow the codebook described in Section 3.2 of the manuscript.

```text
You are classifying construction-industry research abstracts into exactly ONE category.

Categories:
1) Not Related
2) Uncertain
3) AI Development and Methods
4) AI Adoption Factors
5) AI Performance Evaluation
6) AI Economic and Business Impacts

Decision rules:
- Papers that do not substantially address AI or ML applications in construction. AI is mentioned only peripherally or is unrelated to construction contexts ==> Not Related
- Papers with unclear relevance to AI/ML in construction due to vague terms (e.g., "smart systems") or insufficient implementation details ==> Uncertain
- Papers focused on designing, adapting, or advancing AI/ML algorithms or computational approaches tailored to construction-related problems, including specific applications like design optimisation, scheduling, or BIM integration ==> AI Development and Methods
- Papers exploring factors influencing AI/ML adoption in construction, including challenges (e.g., cost, resistance) and benefits/enablers (e.g., efficiency gains) ==> AI Adoption Factors
- Papers that benchmark, validate, or compare AI/ML systems against traditional methods in construction, using simulations or real-world data ==> AI Performance Evaluation
- Papers analysing the economic or business implications of AI/ML in construction, such as ROI or firm competitiveness ==> AI Economic and Business Impacts

Output must strictly follow the JSON schema.
The reason must reference concrete cues from the abstract.
```

---

## Appendix B — Output JSON Schema (Verbatim)

The model output was constrained to the following JSON schema (`additionalProperties: false`), enforced via the API's structured-output mode:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "category": {
      "type": "string",
      "enum": [
        "Not Related",
        "Uncertain",
        "AI Development and Methods",
        "AI Adoption Factors",
        "AI Performance Evaluation",
        "AI Economic and Business Impacts"
      ]
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "reason": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "category",
    "confidence",
    "reason"
  ]
}
```

> [!NOTE]
> *Gemini Pro* responses were observed to populate `confidence` on a 1–10 scale despite the `[0,1]` schema constraint; this is handled via per-model min-max normalisation in the reported confidence-based analyses.
