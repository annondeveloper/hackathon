# ClaimClear AI — Demo Video Generation Prompt

Use the following prompt with **Google Gemini** or a similar AI video tool
to create a professional demo video.

---

## Video Generation Prompt

```
Create a 60-90 second professional product demo video for "ClaimClear AI",
an AI-powered insurance claim explanation assistant built with an agentic
pipeline, RAG grounding, and self-evaluation.

The video should have a modern, clean corporate aesthetic with a blue-to-teal
gradient color scheme.

VIDEO STRUCTURE:

SCENE 1 (0-10s) — Opening
- Animated logo reveal: a shield icon with "ClaimClear AI" text
- Tagline: "Making insurance decisions crystal clear"
- Background: gradient from navy (#0f4c81) to teal (#17a2b8)
- Professional background music

SCENE 2 (10-20s) — The Problem
- Split screen:
  - Left: Customer reading dense insurance letter with highlighted jargon
    ("subrogation", "contestability", "deductible aggregate")
  - Right: Customer service rep on phone, long queue indicator
- Text: "Complex decisions → Confused customers → Costly support calls"

SCENE 3 (20-45s) — The Solution Demo
- Screen recording of ClaimClear AI Streamlit interface:
  1. User selects "Denied Health — Out-of-Network" from dropdown
  2. Form auto-fills: Claim ID, Customer Name, Amount $4,750
  3. User enters API key in sidebar (show password dots)
  4. Click "Generate Explanation" button
  5. Show pipeline stages appearing:
     "Analyzing claim..." → "Generating (RAG-grounded)..." →
     "Self-evaluating quality..." → Done
  6. Clear explanation letter appears in blue card
  7. Quality metrics: Accuracy 9/10, Empathy 8/10, Readability 9/10
  8. Glossary section with defined terms
  9. Expand "Pipeline Details" to show stage-by-stage output

SCENE 4 (45-60s) — AI Pipeline Architecture
- Animated flow diagram:
  Stage 1: ANALYZE (brain icon) → extract key factors
  Stage 2: GENERATE (document icon) ← RAG context from Policy Store
  Stage 3: EVALUATE (checkmark icon) → quality scores
  Stage 4: REFINE (refresh icon) → only if score < 7/10
- Text: "4-stage agentic pipeline with RAG and self-evaluation"
- Highlight: "Catches errors before they reach the customer"

SCENE 5 (60-75s) — Key Metrics
- Animated statistics:
  - "9/10 Accuracy Score" (target icon)
  - "< 3,000 Tokens per Explanation" (coin icon)
  - "30% Fewer Support Calls" (phone icon)
  - "< 10 Seconds to Generate" (clock icon)

SCENE 6 (75-90s) — Closing
- Return to gradient background
- Logo + tagline centered
- Text: "Agentic AI · RAG Grounding · Self-Evaluation"
- "Built at the AI Prototype Challenge"
- Fade to black

STYLE:
- Colors: Navy (#0f4c81), Teal (#17a2b8), White, Light blue (#f8fbff)
- Font: Clean sans-serif (Inter or similar)
- Transitions: Smooth fades and slides
- Music: Upbeat professional corporate
- Aspect ratio: 16:9, 1080p
```

---

## Screen Recording Guide (Manual Demo)

If creating a screen recording instead of a generated video:

### Setup

1. Open the app in Chrome (clean browser, no bookmarks bar)
2. Set browser zoom to 90% for optimal capture
3. Use OBS, Loom, or QuickTime for recording
4. Resolution: 1920x1080

### Recording Script

1. **Show the empty app** (2 seconds)
2. **Select sample claim** — pick "Denied Health — Out-of-Network" (3 seconds)
3. **Point out sidebar** — model, tone, reading level settings (3 seconds)
4. **Enter API key** — type or paste in sidebar password field (3 seconds)
5. **Click "Generate Explanation"** (1 second)
6. **Show pipeline stages** — each stage status updating in real-time (8 seconds)
7. **Read the explanation** — scroll through slowly (10 seconds)
8. **Show quality metrics** — accuracy, empathy, readability, completeness (5 seconds)
9. **Show glossary** — expand a few terms (5 seconds)
10. **Expand pipeline details** — show analysis, RAG info, evaluation (10 seconds)
11. **Click "Download Explanation"** (2 seconds)
12. **Show token usage** in pipeline stats bar (3 seconds)

**Total: ~55 seconds.** Add intro/outro slides for a 90-second video.

### Narration Script

> "ClaimClear AI transforms complex insurance claim decisions into clear
> explanations that customers can understand.
>
> Watch as we load a denied health claim. The AI pipeline analyzes the claim,
> retrieves relevant policy knowledge, generates a personalized explanation,
> and then evaluates its own output for quality.
>
> The result: a clear letter scoring 9 out of 10 on accuracy, with a
> glossary of key terms and concrete next steps for the customer.
>
> All in under 10 seconds, using fewer than 3,000 tokens."
