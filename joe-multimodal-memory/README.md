# SAHAYAK — Multimodal + Memory/Knowledge Base Module

**Team Member:** Joe  
**Role:** Multimodal + Memory/Knowledge Base Lead  
**Component:** Part of the larger SAHAYAK (Smart AI Health & Study Assistant Yielding Actionable Knowledge) project

---

## 🏛 Architecture Overview

```
User Input (image / topic / conversation)
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│               joe-multimodal-memory/                         │
│                                                             │
│  Part A: part_a_image_understanding.py                      │
│  ├── Claude Vision API (base64 image → structured output)   │
│  └── Gemini Vision comparison (live or simulated)           │
│                                                             │
│  Part B: part_b_infographic_generator.py                    │
│  ├── Claude generates JSON revision content                 │
│  └── Python renders → printable HTML infographic            │
│                                                             │
│  Part C: part_c_memory_knowledge_base.py                    │
│  ├── pypdf parses syllabus PDF → topic list                 │
│  ├── Topic list injected into system prompt                 │
│  └── 5-turn memory test via conversation_history            │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
    test_logs/  (markdown logs for each part)
    output/     (generated HTML infographics, JSON payloads)
```

---

## 📁 File Structure

| File | Purpose |
|------|---------|
| `generate_sample_data.py` | Generates `sample_timetable.png` and `sample_syllabus.pdf` with Pillow + ReportLab |
| `part_a_image_understanding.py` | Sends timetable image to Claude Vision, extracts structure, compares with Gemini |
| `part_b_infographic_generator.py` | Claude generates JSON revision content → rendered as printable HTML |
| `part_c_memory_knowledge_base.py` | Parses syllabus PDF, runs 5-turn memory test via Claude conversation |
| `sample_data/sample_timetable.png` | Auto-generated Mon–Fri class timetable image (6 subjects) |
| `sample_data/sample_syllabus.pdf` | Auto-generated CS101 syllabus PDF with 12 topics |
| `test_logs/part_a_log.md` | Part A execution log: table extraction, cross-LLM comparison |
| `test_logs/part_b_log.md` | Part B execution log: generation metadata, JSON payload, evaluation |
| `test_logs/part_c_log.md` | Part C execution log: 5-turn conversation, memory pass/fail |
| `output/` | Generated HTML infographics and JSON payloads |
| `.env.example` | Environment variable template |
| `requirements.txt` | Python dependencies |

---

## 🔑 Required API Keys & Configuration

Create a `.env` file in this directory:

```bash
cp .env.example .env
```

| Variable | Required? | Where to Get | Description |
|---|:---:|---|---|
| `ANTHROPIC_API_KEY` | **Yes** (for live calls) | [Anthropic Console](https://console.anthropic.com/settings/keys) | Powers all three Parts via Claude Vision + Messages API |
| `ANTHROPIC_MODEL` | Optional | — | Default: `claude-3-5-sonnet-20241022` |
| `GOOGLE_API_KEY` | Optional | [AI Studio](https://aistudio.google.com/app/apikey) | Only for Part A live Gemini comparison |

> [!NOTE]
> If `ANTHROPIC_API_KEY` is not set, **all three parts fall back to a rich offline simulation** that demonstrates the full workflow without making API calls. This matches Jackson's offline-first design from the tool-use module.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Sample Data Files
Creates the timetable PNG and syllabus PDF used by Parts A and C:
```bash
python generate_sample_data.py
```

### 3. Run Part A — Timetable Image Understanding
```bash
python part_a_image_understanding.py                        # uses sample image
python part_a_image_understanding.py path/to/timetable.png  # your own image
```

### 4. Run Part B — Revision Infographic Generator
```bash
python part_b_infographic_generator.py                          # interactive
python part_b_infographic_generator.py "Newton's Laws of Motion"
python part_b_infographic_generator.py "Photosynthesis"
python part_b_infographic_generator.py "The French Revolution"
```
Then open `output/revision_<topic>.html` in any browser. It's fully printable (Ctrl+P → Save as PDF → A4).

### 5. Run Part C — 5-Turn Memory Test
```bash
python part_c_memory_knowledge_base.py
```

---

## 🧪 Test Coverage

### Part A — Multimodal Input (Image Understanding)

**Test:** Upload `sample_timetable.png` (5×5 Mon–Fri timetable grid)

**Expected Claude behavior:**
- ✅ Extract all subjects, days, and times into a markdown table
- ✅ Count hours per subject across the week
- ✅ Identify least-studied subject (English/Physics tied at 4 periods)
- ✅ Provide an evidence-based study tip for that subject
- ✅ Maintain Sahayak warm persona throughout

**Cross-LLM Comparison:**

| Criterion | Claude (Anthropic) | Gemini (Google) |
|---|---|---|
| Table extraction accuracy | ✅ | ✅ |
| Hour counting | ✅ Full table | ⚠️ List only |
| Persona adherence | ✅ Strong | ⚠️ Reverts to neutral |
| Actionable tip + citation | ✅ | ⚠️ Generic only |
| Handwriting recognition | ✅ Good (printed) | ✅ Better (cursive) |

---

### Part B — Multimodal Output (Infographic Generation)

**Prompt sent to Claude:**
> "Create a one-page visual revision summary (infographic-style) for the topic '[X]' — use headings, bullet icons, and a clean layout I could print and stick on my wall."

**Claude's approach:**
1. Returns a JSON payload with: topic, color_theme, key_definition, sections[], mnemonic, quick_quiz[], source_citations, exam_tip
2. Python renders the JSON into a standalone HTML page with:
   - A4-sized layout with print CSS
   - Color-coded section cards (2-column grid)
   - Mnemonic memory trick box
   - Quick self-quiz with answers
   - Exam tip callout
   - Source citations in footer

**Topics tested:** Newton's Laws of Motion, Photosynthesis (see `output/` folder)

---

### Part C — Document-Grounded Memory (5-Turn Test)

**Syllabus:** CS101 — 12 topics loaded from `sample_data/sample_syllabus.pdf`

**5-Turn Script:**

| Turn | User Action | Expected Model Behavior |
|:---:|---|---|
| 1 | "List all topics in my syllabus" | Lists all 12 correctly |
| 2 | Marks topics 1 & 2 as covered | Acknowledges, updates tracking |
| 3 | Asks recap of covered topic | Recaps but does NOT add back to to-do list |
| 4 | Marks topics 3 & 4 as covered | Acknowledges 4 total done |
| **5** | "What's left to study?" | **Lists ONLY the 8 remaining topics** — no false re-suggestions |

**Memory evaluation at Turn 5:**
- ❌ False re-suggestions: 0 (covered topics must NOT appear)
- ✅ Remaining topics: 8/8 correctly listed

---

## 📋 Limitations & Responsible Use

### Memory Limitations
- **Context window bounded:** Claude tracks covered topics via conversation history only — not persistent storage. In very long sessions (20+ turns), early "covered" markers may lose attention weight.
- **Mitigation:** Periodically inject a summary message like: "Current status: Topics 1–4 are marked done." This re-anchors Claude's tracking without requiring external memory.

### Multimodal Limitations
- **Image quality matters:** Blurry, low-contrast, or poorly lit photos of handwritten notes significantly reduce extraction accuracy across all models.
- **Handwriting gap:** Claude performs well on printed text; Gemini has an edge on cursive handwriting. For real-world handwritten notes, Gemini Vision is recommended for Part A.
- **Language assumption:** Both models assume English content. Non-English timetables or syllabus PDFs may produce partial or incorrect extractions.

### Infographic Limitations
- **Factual accuracy:** The infographic content is generated by an LLM and should be verified against authoritative sources before use in exam preparation. Always check the citations listed.
- **Hallucination risk:** For niche or advanced topics, Claude may generate plausible-sounding but incorrect facts. The `source_citations` field helps users know where to verify.

### Responsible Use Notes
- This module is a **study aid**, not a replacement for human teachers, textbooks, or official course materials.
- The syllabus grounding (Part C) only works within a single conversation session — it does not persist to a database. Students should not rely on it as a permanent record of progress.
- The infographic (Part B) should be reviewed before printing — it is AI-generated content and may need corrections.

---

## 🔗 Integration with Jackson's Module

Both modules share:
- The same base **Sahayak system prompt** (Uttam's design)
- The same **Anthropic API** (`claude-3-5-sonnet-20241022`)
- The same **`.env` key format** (copy Jackson's `.env` across)
- The same **offline-first fallback design** (runs without API key)

Jackson's module handles: `get_weather`, `calculate_study_schedule`, `search_topic_summary`  
Joe's module handles: `vision_analyze_image`, `generate_infographic`, `memory_track_syllabus`

---

*SAHAYAK — Smart AI Health & Study Assistant Yielding Actionable Knowledge*
