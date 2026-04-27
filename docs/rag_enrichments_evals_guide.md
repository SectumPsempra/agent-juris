# RAG Enrichment, Evaluations, and Frontend Testing

> **What this covers:** How to expand the RAG corpus (`data/raw/` → ingestion → `data/vector_db/`), how **`backend/evals/golden_cases.json`** is structured (the repo currently ships **11** golden cases — 3 seed scenarios plus **8** additional statutes‑grounded cases), optional manual UI checks, and **Vitest** setup for frontend unit/component tests.

> **Previous revision:** Older versions used “8 new cases only” wording and session-specific framing; the archived revision is not included in this repository.

---

## Table of Contents

1. [Expanding the RAG Corpus](#1-expanding-the-rag-corpus)
2. [Current RAG Corpus](#2-current-rag-corpus)
3. [Golden Evaluation Cases](#3-golden-evaluation-cases)
   - 3.1 [How to add them](#31-how-to-add-them)
   - 3.2 [Golden case JSON examples](#32-golden-case-json-examples)
4. [Frontend Manual Test Cases](#4-frontend-manual-test-cases)
5. [Frontend Automated Tests — Vitest Setup](#5-frontend-automated-tests--vitest-setup)
   - 5.1 [Install and configure](#51-install-and-configure)
   - 5.2 [Unit tests for `agent-step-markdown.ts`](#52-unit-tests-for-agent-step-markdownts)
   - 5.3 [Component tests for `PipelineMarkdownPanel`](#53-component-tests-for-pipelinemarkdownpanel)
   - 5.4 [Running the tests](#54-running-the-tests)

---

## 1. Expanding the RAG Corpus

### The one-line answer

Copy `.txt` or `.md` files into `data/raw/`, then re-run:

```bash
cd backend
uv run python -m src.rag.ingestion
```

That is all. The ingestion script globs every `.txt` and `.md` file in `data/raw/` automatically on every run.

### Rules for files you add

| Rule | Detail |
|------|--------|
| Accepted formats | `.txt` and `.md` only |
| File naming | Anything descriptive — e.g. `civil_procedure_act_cap21.txt` |
| Content format | Plain text. No special structure needed. Paste the statute text as-is — section numbers, headings, paragraphs all work fine. |
| File size | No hard limit. Large files are fine — the chunker splits them automatically. |
| How many files | No limit. Add as many as you want. |

### What the ingestion script does with your files

1. Reads every `.txt` / `.md` file in `data/raw/`
2. Splits each file into overlapping 800-character chunks (100-char overlap at each boundary)
3. Calls OpenAI's `text-embedding-3-small` model to convert each chunk to a 1536-dimension vector
4. Writes all chunks + vectors into `data/vector_db/` (ChromaDB)

Each run re-indexes everything from scratch, so running it again after adding files is safe — it replaces the old index.

### Tips for text quality

PDF-exported text sometimes has garbled line breaks or headers mixed into body paragraphs. If you paste from a PDF, do a quick scan for obvious formatting issues. Clean text → better embeddings → better retrieval.

### Recommended additional documents (all free on kenyalaw.org)

These are the ones most likely to improve strategy and drafting quality for common Kenyan litigation matters:

| Document | Filename suggestion | Useful for |
|----------|---------------------|-----------|
| Civil Procedure Act, Cap 21 | `civil_procedure_act_cap21.txt` | All civil litigation procedure |
| Land Registration Act, No. 3 of 2012 | `land_registration_act_2012.txt` | Land title and registration |
| Judicature Act, Cap 8 | `judicature_act_cap8.txt` | Court hierarchy and jurisdiction |
| Limitation of Actions Act | `limitation_of_actions_act.txt` | Time limits on claims |
| Public Procurement Act, 2015 | `public_procurement_act_2015.txt` | Government contract disputes |
| Arbitration Act, No. 4 of 1995 | `arbitration_act_cap49.txt` | Commercial arbitration |
| Marriage Act, No. 4 of 2014 | `marriage_act_cap150.txt` | Family law |
| Succession Act, Cap 160 | `succession_act_cap160.txt` | Wills and estates |
| Constitution of Kenya, 2010 | `constitution_of_kenya_2010.txt` | Bill of Rights, judicial review |

---

## 2. Current RAG Corpus

As of **2026-04-22**, `data/raw/` contains **15** Kenyan law text files (plus a `.gitkeep`). Filenames drift slightly over time — always list the directory if you need an exact manifest:

| Filename | Legal domain |
|----------|-------------|
| `arbitration_act_cap49.txt` | Arbitration — stay of proceedings, arbitral awards |
| `civil_procedure_act_cap21.txt` | Civil procedure — jurisdiction, res judicata, enforcement |
| `constitution_of_kenya_2010.txt` | Constitutional rights — Bill of Rights, fair hearing, Article 47 |
| `contract_act_cap_23.txt` | Contract law — written contracts, part performance |
| `criminal_procedure_code_cap75.txt` | Criminal procedure |
| `employment_act_2007.txt` | Employment — termination, dismissal, wages, harassment |
| `judicature_act_cap_8.txt` | Court jurisdiction and hierarchy |
| `land_act_2012.txt` | Land — leases, charges, compulsory acquisition |
| `law_of_torts_basic.txt` | Tort — negligence, nuisance, occupier's liability |
| `limitation_of_actions_act.txt` | Limitation periods for contract and tort claims |
| `marriage_act_cap150.txt` | Marriage — void/voidable marriages, dissolution |
| `penal_code_cap63.txt` | Criminal offences |
| `public_procurement_and_asset_disposal_act_cap412c.txt` | Government procurement disputes |
| `small_claims_court_act.txt` | Small claims procedure |
| `succession_act_cap_160.txt` | Wills, estates, probate, intestacy |

---

## 3. Golden Evaluation Cases

### 3.1 How to add them

Open `backend/evals/golden_cases.json`. It is a JSON array. Append new objects alongside the **11** cases already committed (`land-001`, `supply-001`, `employment-001`, `arb-001`, `tort-001`, `lim-001`, `succ-001`, `marr-001`, `cpa-001`, `const-001`, `proc-001`). Re-run the eval commands after editing.

Then run either eval script:

```bash
cd backend

# Extraction eval — checks structured output against constraints (free, fast)
uv run python -m evals.eval_extraction

# LLM-as-judge eval — scores full pipeline output 1–5 on 3 dimensions (~$0.30+ per full run over all golden cases)
uv run python -m evals.eval_llm_judge
```

**GitHub Actions (`evals.yml`):** On path-filtered pushes to **`main`**, **`eval_extraction`** runs against every row in **`backend/evals/golden_cases.json`** (**11** golden cases). The **`extraction-eval`** job uses **`continue-on-error: true`**, so the workflow does not block merges when the eval fails or **`OPENAI_API_KEY`** is missing—use the job log for pass/fail. To block merges on golden-case regression, add **`OPENAI_API_KEY`** as a repo secret and remove **`continue-on-error`**. **`eval_llm_judge`** runs only via **Actions → Evaluations → Run workflow** with the optional checkbox (~**$0.30+** per full run). See **`docs/PROJECT_WALKTHROUGH.md`** §22 for tables and rubric mapping.

### 3.2 Golden case JSON examples

The block below shows the **shape** of each golden case (`id`, `description`, `case_text`, nested `expected` constraints). The repository **already includes** these scenarios (and more) in `golden_cases.json` — keep this section as a reference when authoring **additional** cases, not as something you must paste wholesale.

```json
  {
    "id": "arb-001",
    "description": "Arbitration — court proceedings filed despite arbitration clause",
    "case_text": "Savannah Logistics Ltd and Rift Valley Warehousing Ltd entered into a warehousing services agreement on 2 February 2022. Clause 18 of the agreement required all disputes to be referred to arbitration under the Arbitration Act, Cap 49, with the seat in Nairobi. On 14 November 2023 Savannah filed suit in the High Court at Nairobi claiming KES 3,200,000 for loss of goods damaged during storage. Rift Valley filed an application under section 6 of the Arbitration Act seeking a stay of the court proceedings and referral of the dispute to arbitration. Savannah argues the arbitration clause is null because Rift Valley was in breach of contract at the time the clause was invoked. Rift Valley denies breach and insists the clause is binding.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Savannah Logistics Ltd", "Rift Valley Warehousing Ltd"],
      "required_entity_types": ["company"],
      "min_timeline_events": 3,
      "timeline_must_contain_date_prefix": "2022-02-02",
      "expected_keywords_in_facts": ["arbitration", "stay", "KES 3,200,000"]
    }
  },
  {
    "id": "tort-001",
    "description": "Negligence — construction site injury, occupier's liability",
    "case_text": "Peter Otieno was employed as a casual labourer by Nyati Construction Ltd on a building site in Westlands, Nairobi. On 8 June 2023, while working on the third floor, Peter fell through an unmarked gap in the floor slab that had not been cordoned off or signed. He sustained a fractured spine and is now partially paralysed. Peter had not been provided with a safety harness or any personal protective equipment. Nyati Construction Ltd claims Peter was warned verbally about the hazard, a claim Peter denies. Peter seeks general damages for pain and suffering, special damages for medical expenses of KES 450,000, and loss of future earnings.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Peter Otieno", "Nyati Construction Ltd", "Westlands"],
      "required_entity_types": ["person", "company", "place"],
      "min_timeline_events": 2,
      "timeline_must_contain_date_prefix": "2023-06-08",
      "expected_keywords_in_facts": ["negligence", "KES 450,000", "protective equipment"]
    }
  },
  {
    "id": "lim-001",
    "description": "Limitation of actions — contract debt claim filed out of time",
    "case_text": "On 1 March 2014, Baraka Hardware Ltd supplied building materials worth KES 920,000 to Odhiambo Estates Ltd under a written credit agreement, with payment due within 60 days. Odhiambo Estates failed to pay. Baraka sent demand letters on 15 May 2014 and 3 August 2014, both of which were acknowledged in writing by Odhiambo Estates. No payment was made. On 10 November 2022, Baraka filed suit in the High Court to recover the outstanding principal and accrued interest. Odhiambo Estates has filed a preliminary objection arguing the claim is statute-barred under section 4 of the Limitation of Actions Act, as more than six years elapsed from the date payment fell due. Baraka argues the written acknowledgements of 2014 restarted the limitation period under section 23 of the Act.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Baraka Hardware Ltd", "Odhiambo Estates Ltd"],
      "required_entity_types": ["company"],
      "min_timeline_events": 4,
      "timeline_must_contain_date_prefix": "2014-03-01",
      "expected_keywords_in_facts": ["limitation", "KES 920,000", "acknowledgement"]
    }
  },
  {
    "id": "succ-001",
    "description": "Succession — contested will, undue influence and lack of capacity",
    "case_text": "James Muriuki Njenga, a retired civil servant, died on 22 October 2022 in Nyeri County. He left a written will dated 5 September 2022 that bequeathed his entire estate, valued at approximately KES 12,000,000, to his youngest daughter Eunice Njenga, to the exclusion of his three other adult children. The other children, led by firstborn David Njenga, filed a petition challenging the will in the High Court Probate and Administration Division. They allege that at the time of making the will, their father was suffering from advanced dementia and lacked testamentary capacity under section 5 of the Succession Act. They also allege that Eunice, who was his primary caregiver, exerted undue influence over him. Eunice denies both allegations and has produced a letter from a general practitioner dated 3 September 2022 stating that James was of sound mind.",
    "expected": {
      "min_core_facts": 5,
      "required_entity_names": ["James Muriuki Njenga", "Eunice Njenga", "David Njenga", "Nyeri County"],
      "required_entity_types": ["person", "place"],
      "min_timeline_events": 3,
      "timeline_must_contain_date_prefix": "2022-09-05",
      "expected_keywords_in_facts": ["will", "undue influence", "testamentary capacity", "KES 12,000,000"]
    }
  },
  {
    "id": "marr-001",
    "description": "Marriage — nullity petition, subsisting marriage not disclosed",
    "case_text": "Amina Hassan and Ibrahim Salim celebrated a civil marriage at the Mombasa Registrar of Marriages on 14 February 2020. Amina was unaware at the time that Ibrahim had contracted a prior civil marriage with one Fatuma Omar in 2015, which had never been dissolved. Amina discovered the prior subsisting marriage in January 2024 after Fatuma filed a succession claim against Ibrahim's estate following his death. Amina now seeks a declaration that her marriage to Ibrahim is void ab initio under section 11(a) of the Marriage Act on the grounds that Ibrahim was incapable of marriage due to a prior subsisting civil marriage. She also seeks ancillary relief relating to matrimonial property acquired jointly during the marriage.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Amina Hassan", "Ibrahim Salim", "Fatuma Omar", "Mombasa"],
      "required_entity_types": ["person", "place"],
      "min_timeline_events": 3,
      "timeline_must_contain_date_prefix": "2020-02-14",
      "expected_keywords_in_facts": ["void", "subsisting marriage", "nullity"]
    }
  },
  {
    "id": "cpa-001",
    "description": "Civil Procedure — res judicata, second suit on same cause of action",
    "case_text": "In 2019, Kipchoge Investments Ltd filed suit against Meridian Bank Ltd in the Nairobi High Court claiming KES 8,500,000 for wrongful dishonour of cheques, causing loss of a business deal. The suit was heard on its merits and dismissed by the High Court in a judgment delivered on 3 March 2021. Kipchoge did not appeal. On 10 January 2024, Kipchoge filed a fresh suit in the Commercial Division raising substantially the same facts and same cause of action but framing the claim as one in tort for negligence. Meridian Bank has filed a preliminary objection that the second suit is barred by res judicata under section 7 of the Civil Procedure Act, as the matter was directly and substantially in issue in the earlier suit, which was decided by a competent court between the same parties.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Kipchoge Investments Ltd", "Meridian Bank Ltd"],
      "required_entity_types": ["company"],
      "min_timeline_events": 3,
      "timeline_must_contain_date_prefix": "2021-03-03",
      "expected_keywords_in_facts": ["res judicata", "KES 8,500,000", "dismissed"]
    }
  },
  {
    "id": "const-001",
    "description": "Constitutional petition — unlawful termination, right to fair hearing",
    "case_text": "Dr. Naliaka Simiyu was employed as a consultant physician at Eldoret General Hospital, a public facility run by Uasin Gishu County Government, under a three-year renewable contract. On 2 May 2023, she was issued a letter of termination citing restructuring with immediate effect and no compensation. She had not been given any show-cause notice, opportunity to be heard, or reasons for her termination. Dr. Simiyu filed a constitutional petition under Article 22 and Article 50(1) of the Constitution of Kenya 2010, alleging violation of her right to fair administrative action under Article 47 and her right to fair hearing before termination. She also alleges the termination was linked to her public complaint about inadequate medical supplies at the hospital, engaging her freedom of expression under Article 33.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Dr. Naliaka Simiyu", "Eldoret General Hospital", "Uasin Gishu County Government"],
      "required_entity_types": ["person", "government_body", "place"],
      "min_timeline_events": 2,
      "timeline_must_contain_date_prefix": "2023-05-02",
      "expected_keywords_in_facts": ["fair hearing", "Article 47", "termination", "constitutional petition"]
    }
  },
  {
    "id": "proc-001",
    "description": "Public procurement — irregular tender award, challenge by aggrieved bidder",
    "case_text": "Silverline Technologies Ltd submitted a tender for the supply and installation of ICT equipment at Kenya Revenue Authority offices, Tender No. KRA/ICT/2023/041, with a bid of KES 47,000,000. The tender was awarded to Maxcom Solutions Ltd at KES 52,000,000, despite Maxcom's bid being higher and Silverline having scored higher on the technical evaluation. Silverline filed a request for review before the Public Procurement Administrative Review Board under section 167 of the Public Procurement and Asset Disposal Act, arguing that the evaluation committee failed to apply the criteria set out in the tender documents, and that Maxcom did not meet the mandatory technical specifications. KRA contends the award was based on additional undisclosed evaluation factors permitted under the tender regulations.",
    "expected": {
      "min_core_facts": 4,
      "required_entity_names": ["Silverline Technologies Ltd", "Maxcom Solutions Ltd", "Kenya Revenue Authority"],
      "required_entity_types": ["company", "government_body"],
      "min_timeline_events": 2,
      "timeline_must_contain_date_prefix": "2023",
      "expected_keywords_in_facts": ["tender", "KES 47,000,000", "evaluation", "review"]
    }
  }
```

---

## 4. Frontend Manual Test Cases

These are ready to paste directly into the `/dashboard/new-scan` form. Copy the title into the **Title** field and the case text into the **Case text** textarea.

After each run, check these things in the output:

| Pipeline step | What good output looks like |
|---------------|-----------------------------|
| **Extraction** | Correct party names, right entity types (company / government_body / person / place), ISO dates in timeline |
| **RAG retrieval** | Relevant statute sections pulled — e.g. case 3 should retrieve Limitation of Actions Act, case 7 should retrieve Constitution articles |
| **Strategy** | Legal issues match the domain; statute citations are specific (Cap number + section) |
| **QA risk level** | Should be LOW or MEDIUM; HIGH means the model added a fact not in the input |

---

### Case 1 — Arbitration stay
**Title:** `Savannah Logistics Ltd v Rift Valley Warehousing Ltd`

**Case text:**
```
Savannah Logistics Ltd and Rift Valley Warehousing Ltd entered into a warehousing services agreement on 2 February 2022. Clause 18 of the agreement required all disputes to be referred to arbitration under the Arbitration Act, Cap 49, with the seat in Nairobi. On 14 November 2023, Savannah filed suit in the High Court at Nairobi claiming KES 3,200,000 for loss of goods damaged during storage. Rift Valley filed an application under section 6 of the Arbitration Act seeking a stay of the court proceedings and referral of the dispute to arbitration. Savannah argues the arbitration clause is null because Rift Valley was in breach of contract at the time the clause was invoked. Rift Valley denies breach and insists the clause is binding.
```

---

### Case 2 — Negligence / personal injury
**Title:** `Peter Otieno v Nyati Construction Ltd`

**Case text:**
```
Peter Otieno was employed as a casual labourer by Nyati Construction Ltd on a building site in Westlands, Nairobi. On 8 June 2023, while working on the third floor, Peter fell through an unmarked gap in the floor slab that had not been cordoned off or signed. He sustained a fractured spine and is now partially paralysed. Peter had not been provided with a safety harness or any personal protective equipment. Nyati Construction Ltd claims Peter was verbally warned about the hazard, a claim Peter denies. Peter seeks general damages for pain and suffering, special damages for medical expenses of KES 450,000, and loss of future earnings.
```

---

### Case 3 — Limitation of actions
**Title:** `Baraka Hardware Ltd v Odhiambo Estates Ltd`

**Case text:**
```
On 1 March 2014, Baraka Hardware Ltd supplied building materials worth KES 920,000 to Odhiambo Estates Ltd under a written credit agreement, with payment due within 60 days. Odhiambo Estates failed to pay. Baraka sent demand letters on 15 May 2014 and 3 August 2014, both acknowledged in writing by Odhiambo Estates. No payment was made. On 10 November 2022, Baraka filed suit in the High Court to recover the outstanding principal and accrued interest. Odhiambo Estates has filed a preliminary objection arguing the claim is statute-barred under section 4 of the Limitation of Actions Act, as more than six years elapsed from the date payment fell due. Baraka argues the written acknowledgements restarted the limitation period under section 23 of the Act.
```

---

### Case 4 — Contested will
**Title:** `In re Estate of James Muriuki Njenga`

**Case text:**
```
James Muriuki Njenga, a retired civil servant, died on 22 October 2022 in Nyeri County. He left a written will dated 5 September 2022 bequeathing his entire estate, valued at approximately KES 12,000,000, to his youngest daughter Eunice Njenga, to the exclusion of his three other adult children. The other children, led by firstborn David Njenga, filed a petition challenging the will in the High Court Probate and Administration Division. They allege that at the time of making the will their father was suffering from advanced dementia and lacked testamentary capacity under section 5 of the Succession Act. They also allege that Eunice, who was his primary caregiver, exerted undue influence over him. Eunice denies both allegations and has produced a letter from a general practitioner dated 3 September 2022 stating that James was of sound mind.
```

---

### Case 5 — Void marriage
**Title:** `Amina Hassan v Estate of Ibrahim Salim`

**Case text:**
```
Amina Hassan and Ibrahim Salim celebrated a civil marriage at the Mombasa Registrar of Marriages on 14 February 2020. Amina was unaware at the time that Ibrahim had contracted a prior civil marriage with one Fatuma Omar in 2015, which had never been dissolved. Amina discovered the prior subsisting marriage in January 2024 after Fatuma filed a succession claim against Ibrahim's estate following his death. Amina now seeks a declaration that her marriage to Ibrahim is void ab initio under section 11(a) of the Marriage Act on the grounds that Ibrahim was incapable of marriage due to a prior subsisting civil marriage. She also seeks ancillary relief relating to matrimonial property acquired jointly during the marriage.
```

---

### Case 6 — Res judicata
**Title:** `Kipchoge Investments Ltd v Meridian Bank Ltd`

**Case text:**
```
In 2019, Kipchoge Investments Ltd filed suit against Meridian Bank Ltd in the Nairobi High Court claiming KES 8,500,000 for wrongful dishonour of cheques, causing loss of a business deal. The suit was heard on its merits and dismissed by the High Court in a judgment delivered on 3 March 2021. Kipchoge did not appeal. On 10 January 2024, Kipchoge filed a fresh suit in the Commercial Division raising substantially the same facts and same cause of action but framing the claim as one in tort for negligence. Meridian Bank has filed a preliminary objection that the second suit is barred by res judicata under section 7 of the Civil Procedure Act, as the matter was directly and substantially in issue in the earlier suit, which was decided by a competent court between the same parties.
```

---

### Case 7 — Constitutional petition
**Title:** `Dr. Naliaka Simiyu v Uasin Gishu County Government`

**Case text:**
```
Dr. Naliaka Simiyu was employed as a consultant physician at Eldoret General Hospital, a public facility run by Uasin Gishu County Government, under a three-year renewable contract. On 2 May 2023, she was issued a letter of termination citing restructuring, with immediate effect and no compensation. She had not been given any show-cause notice, opportunity to be heard, or reasons for her termination. Dr. Simiyu filed a constitutional petition under Article 22 and Article 50(1) of the Constitution of Kenya 2010, alleging violation of her right to fair administrative action under Article 47 and her right to fair hearing before termination. She also alleges the termination was linked to her public complaint about inadequate medical supplies at the hospital, engaging her freedom of expression under Article 33.
```

---

### Case 8 — Procurement tender challenge
**Title:** `Silverline Technologies Ltd v Kenya Revenue Authority`

**Case text:**
```
Silverline Technologies Ltd submitted a tender for the supply and installation of ICT equipment at Kenya Revenue Authority offices, Tender No. KRA/ICT/2023/041, with a bid of KES 47,000,000. The tender was awarded to Maxcom Solutions Ltd at KES 52,000,000, despite Maxcom's bid being higher and Silverline having scored higher on the technical evaluation. Silverline filed a request for review before the Public Procurement Administrative Review Board under section 167 of the Public Procurement and Asset Disposal Act, arguing that the evaluation committee failed to apply the criteria set out in the tender documents, and that Maxcom did not meet the mandatory technical specifications. KRA contends the award was based on additional undisclosed evaluation factors permitted under the tender regulations.
```

---

## 5. Frontend Automated Tests — Vitest Setup

No test framework exists in the frontend yet. The setup below adds Vitest (works natively with Next.js 16 + TypeScript, no Webpack/Babel config needed).

### 5.1 Install and configure

```bash
cd frontend
npm install --save-dev vitest @vitest/coverage-v8 @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

Add to `frontend/package.json`:

```json
"scripts": {
  "test": "vitest",
  "test:coverage": "vitest run --coverage"
},
"vitest": {
  "environment": "jsdom",
  "setupFiles": ["./src/test/setup.ts"],
  "globals": true
}
```

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom";
```

Run tests:

```bash
npm test               # watch mode — re-runs on file save
npm run test:coverage  # single pass with line coverage report
```

---

### 5.2 Unit tests for `agent-step-markdown.ts`

**Why this file?** It is pure TypeScript — no React, no network, no Clerk. It mirrors `backend/src/agents/format_markdown.py` exactly. Every function takes a plain object and returns a Markdown string. Deterministic, zero mocking needed.

**File to create:** `frontend/src/lib/__tests__/agent-step-markdown.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { stepResultToMarkdown, STEP_HEADINGS } from "../agent-step-markdown";

// ── STEP_HEADINGS ─────────────────────────────────────────────────────────────

describe("STEP_HEADINGS", () => {
  it("has an entry for all five pipeline steps", () => {
    for (const step of ["extraction", "rag_retrieval", "strategy", "drafting", "qa"]) {
      expect(STEP_HEADINGS[step]).toBeDefined();
    }
  });

  it("returns undefined for unknown step names", () => {
    expect(STEP_HEADINGS["unknown_step"]).toBeUndefined();
  });
});

// ── null / unknown ────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — null and unknown", () => {
  it("returns null when result is null", () => {
    expect(stepResultToMarkdown("extraction", null)).toBeNull();
  });

  it("returns null for an unrecognised step name", () => {
    expect(stepResultToMarkdown("not_a_step", { foo: "bar" })).toBeNull();
  });
});

// ── extraction ────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — extraction", () => {
  const result = {
    core_facts: [
      "John Kamau signed a land sale agreement with Sarah Wanjiru on 15 March 2023",
      "The agreed price was KES 5,000,000",
    ],
    entities: [
      { name: "John Kamau", type: "person", role: "buyer" },
      { name: "Kiambu County", type: "place", role: "jurisdiction" },
    ],
    chronological_timeline: [
      { date: "2023-03-15", event: "Written sale agreement signed" },
    ],
  };

  it("includes the Core facts heading", () => {
    expect(stepResultToMarkdown("extraction", result)).toContain("### Core facts");
  });

  it("renders each fact as a bullet", () => {
    const md = stepResultToMarkdown("extraction", result)!;
    expect(md).toContain("- John Kamau signed a land sale agreement");
    expect(md).toContain("- The agreed price was KES 5,000,000");
  });

  it("renders entity name, type, and role", () => {
    const md = stepResultToMarkdown("extraction", result)!;
    expect(md).toContain("John Kamau");
    expect(md).toContain("person");
    expect(md).toContain("buyer");
  });

  it("includes the Chronological timeline heading", () => {
    expect(stepResultToMarkdown("extraction", result)).toContain("### Chronological timeline");
  });

  it("renders timeline date and event", () => {
    const md = stepResultToMarkdown("extraction", result)!;
    expect(md).toContain("2023-03-15");
    expect(md).toContain("Written sale agreement signed");
  });

  it("handles empty core_facts gracefully", () => {
    expect(stepResultToMarkdown("extraction", { ...result, core_facts: [] }))
      .toContain("### Core facts");
  });

  it("skips non-object entity entries without crashing", () => {
    const md = stepResultToMarkdown("extraction", {
      ...result,
      entities: [null, "bad", { name: "Valid", type: "person", role: "claimant" }],
    });
    expect(md).toContain("Valid");
  });
});

// ── rag_retrieval ─────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — rag_retrieval", () => {
  it("shows 'No precedents' when chunks is empty", () => {
    expect(stepResultToMarkdown("rag_retrieval", { chunks: [] })).toContain("No precedents");
  });

  it("shows 'No precedents' when chunks key is missing", () => {
    expect(stepResultToMarkdown("rag_retrieval", {})).toContain("No precedents");
  });

  it("renders 'Retrieved excerpts' heading when chunks present", () => {
    const md = stepResultToMarkdown("rag_retrieval", {
      chunks: ["Section 3(3) of the Law of Contract Act."],
    });
    expect(md).toContain("### Retrieved excerpts");
    expect(md).toContain("Source 1");
  });

  it("numbers multiple chunks correctly", () => {
    const md = stepResultToMarkdown("rag_retrieval", {
      chunks: ["chunk a", "chunk b", "chunk c"],
    });
    expect(md).toContain("Source 1");
    expect(md).toContain("Source 2");
    expect(md).toContain("Source 3");
  });

  it("renders the chunk text content", () => {
    const text = "Section 38 of the Land Act, 2012 — specific performance.";
    expect(stepResultToMarkdown("rag_retrieval", { chunks: [text] })).toContain(text);
  });
});

// ── strategy ──────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — strategy", () => {
  const result = {
    legal_issues: ["Whether the contract is valid"],
    applicable_laws: ["Law of Contract Act, Cap 23 — Section 3(3)"],
    arguments: [
      {
        issue: "Validity of contract",
        applicable_kenyan_law: "Law of Contract Act, Cap 23",
        argument_summary: "Written contract satisfies Section 3(3).",
      },
    ],
    counterarguments: ["Respondent may argue lack of essential terms."],
    legal_reasoning: "The contract is valid under Kenyan law.",
  };

  it("includes Legal issues, Applicable laws, Arguments, Counterarguments, Legal reasoning headings", () => {
    const md = stepResultToMarkdown("strategy", result)!;
    for (const h of ["### Legal issues", "### Applicable laws", "### Arguments", "### Counterarguments", "### Legal reasoning"]) {
      expect(md).toContain(h);
    }
  });

  it("renders argument issue, law, and summary", () => {
    const md = stepResultToMarkdown("strategy", result)!;
    expect(md).toContain("Validity of contract");
    expect(md).toContain("Law of Contract Act, Cap 23");
    expect(md).toContain("Written contract satisfies Section 3(3).");
  });

  it("renders legal reasoning text", () => {
    expect(stepResultToMarkdown("strategy", result)).toContain("The contract is valid under Kenyan law.");
  });

  it("handles empty arguments array without crashing", () => {
    expect(stepResultToMarkdown("strategy", { ...result, arguments: [] }))
      .toContain("### Arguments");
  });
});

// ── drafting ──────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — drafting", () => {
  const brief = `# IN THE MATTER OF John Kamau v Sarah Wanjiru\n\n## PARTIES\nThe Applicant is John Kamau.\n\n## FACTS\nOn 15 March 2023 the parties signed a sale agreement.\n\n## ISSUES FOR DETERMINATION\n1. Whether the agreement is enforceable\n\n## LEGAL ARGUMENTS\n### Validity\nThe agreement is valid.\n\n## RESPONDENT'S ANTICIPATED POSITION\nRespondent contends the contract is void.\n\n## CONCLUSION AND PRAYER FOR RELIEF\nThe Court should grant specific performance.`;

  it("returns the brief_markdown string unchanged", () => {
    expect(stepResultToMarkdown("drafting", { brief_markdown: brief })).toBe(brief.trim());
  });

  it("returns empty string when brief_markdown is empty", () => {
    expect(stepResultToMarkdown("drafting", { brief_markdown: "" })).toBe("");
  });

  it("returns empty string when brief_markdown key is missing", () => {
    expect(stepResultToMarkdown("drafting", {})).toBe("");
  });

  it("preserves all required section headers", () => {
    const md = stepResultToMarkdown("drafting", { brief_markdown: brief })!;
    for (const heading of [
      "## FACTS",
      "## ISSUES FOR DETERMINATION",
      "## LEGAL ARGUMENTS",
      "## RESPONDENT'S ANTICIPATED POSITION",
      "## CONCLUSION AND PRAYER FOR RELIEF",
    ]) {
      expect(md).toContain(heading);
    }
  });
});

// ── qa ────────────────────────────────────────────────────────────────────────

describe("stepResultToMarkdown — qa", () => {
  const base = { hallucination_warnings: [], missing_logic: [], risk_notes: [] };

  it("renders LOW risk level", () => {
    expect(stepResultToMarkdown("qa", { ...base, risk_level: "LOW" })).toContain("LOW");
  });

  it("renders HIGH risk level", () => {
    expect(stepResultToMarkdown("qa", { ...base, risk_level: "HIGH" })).toContain("HIGH");
  });

  it("shows 'None noted' when all lists are empty", () => {
    const md = stepResultToMarkdown("qa", { ...base, risk_level: "LOW" })!;
    expect(md.match(/None noted/g)?.length).toBeGreaterThanOrEqual(3);
  });

  it("renders a populated hallucination warning", () => {
    const warning = "Statute section cited does not exist in the Act.";
    const md = stepResultToMarkdown("qa", {
      ...base,
      risk_level: "HIGH",
      hallucination_warnings: [warning],
    });
    expect(md).toContain(warning);
  });

  it("renders missing logic and risk notes entries", () => {
    const md = stepResultToMarkdown("qa", {
      risk_level: "MEDIUM",
      hallucination_warnings: [],
      missing_logic: ["Issue 2 never argued"],
      risk_notes: ["Review before filing"],
    })!;
    expect(md).toContain("Issue 2 never argued");
    expect(md).toContain("Review before filing");
  });

  it("shows UNKNOWN when risk_level is missing", () => {
    expect(stepResultToMarkdown("qa", { ...base })).toContain("UNKNOWN");
  });
});
```

---

### 5.3 Component tests for `PipelineMarkdownPanel`

**Why this component?** It is the most visible UI element — the collapsible panels that show each agent's output. Tests cover the empty state, section count, heading text, and the Show/Hide toggle.

**File to create:** `frontend/src/components/__tests__/pipeline-markdown-panel.test.tsx`

```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PipelineMarkdownPanel, type MarkdownSection } from "../pipeline-markdown-panel";

const SECTIONS: MarkdownSection[] = [
  { section_id: "extraction", heading: "Fact extraction", markdown: "## Core facts\n- John signed the agreement" },
  { section_id: "strategy", heading: "Legal strategy", markdown: "## Legal issues\n- Contract validity" },
  { section_id: "drafting", heading: "Draft brief", markdown: "# IN THE MATTER OF\n## FACTS\nDetails here." },
];

// ── Empty state ───────────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — empty state", () => {
  it("shows emptyMessage when sections is empty and not streaming", () => {
    render(<PipelineMarkdownPanel sections={[]} emptyMessage="No output yet." />);
    expect(screen.getByText("No output yet.")).toBeInTheDocument();
  });

  it("shows 'Waiting for output…' when sections is empty and streaming=true", () => {
    render(<PipelineMarkdownPanel sections={[]} emptyMessage="No output yet." streaming />);
    expect(screen.getByText("Waiting for output…")).toBeInTheDocument();
  });

  it("renders no <details> elements when sections is empty", () => {
    const { container } = render(
      <PipelineMarkdownPanel sections={[]} emptyMessage="Nothing here." />
    );
    expect(container.querySelectorAll("details")).toHaveLength(0);
  });
});

// ── Sections rendering ────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — sections rendering", () => {
  it("renders one <details> element per section", () => {
    const { container } = render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="" />);
    expect(container.querySelectorAll("details")).toHaveLength(3);
  });

  it("renders each section heading in a <summary>", () => {
    render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="" />);
    expect(screen.getByText("Fact extraction")).toBeInTheDocument();
    expect(screen.getByText("Legal strategy")).toBeInTheDocument();
    expect(screen.getByText("Draft brief")).toBeInTheDocument();
  });

  it("does not show emptyMessage when sections are present", () => {
    render(<PipelineMarkdownPanel sections={SECTIONS} emptyMessage="Nothing here." />);
    expect(screen.queryByText("Nothing here.")).not.toBeInTheDocument();
  });
});

// ── Show / Hide toggle ────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — show/hide toggle", () => {
  it("shows 'Show' label when section is collapsed", () => {
    render(<PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />);
    expect(screen.getByText("Show")).toBeInTheDocument();
  });

  it("shows 'Hide' label after clicking to expand", async () => {
    render(<PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />);
    await userEvent.click(screen.getByText("Fact extraction"));
    expect(screen.getByText("Hide")).toBeInTheDocument();
  });
});

// ── Markdown content ──────────────────────────────────────────────────────────

describe("PipelineMarkdownPanel — markdown content", () => {
  it("renders markdown content after expanding a section", async () => {
    render(<PipelineMarkdownPanel sections={[SECTIONS[0]]} emptyMessage="" />);
    await userEvent.click(screen.getByText("Fact extraction"));
    expect(screen.getByText(/John signed the agreement/)).toBeInTheDocument();
  });

  it("renders a single QA section with risk level text", async () => {
    const qa: MarkdownSection[] = [
      { section_id: "qa", heading: "Quality review", markdown: "**Risk level:** `LOW`" },
    ];
    render(<PipelineMarkdownPanel sections={qa} emptyMessage="" />);
    await userEvent.click(screen.getByText("Quality review"));
    expect(screen.getByText(/LOW/)).toBeInTheDocument();
  });
});
```

---

### 5.4 Running the tests

```bash
cd frontend
npm test                   # watch mode — re-runs on every file save
npm run test:coverage      # single run with line coverage report
```

**Expected output:**
```
 ✓ src/lib/__tests__/agent-step-markdown.test.ts   (42 tests)
 ✓ src/components/__tests__/pipeline-markdown-panel.test.tsx  (12 tests)

 Test Files  2 passed (2)
      Tests  54 passed (54)
   Duration  1.2s
```

**Interpreting failures:**

| Output | What it means |
|--------|---------------|
| `expected "### Core facts" to be in "..."` | The heading text in `agent-step-markdown.ts` was changed — update the test to match the new heading |
| `Unable to find element with text: "Fact extraction"` | The `heading` value in `MarkdownSection` or the component's summary rendering changed |
| `expected 3 to equal 4` on `querySelectorAll("details")` | A section is not being rendered — check the sections array passed to the component |

---

*Session date: April 2026*
