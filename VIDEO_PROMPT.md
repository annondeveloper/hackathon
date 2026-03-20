# ClaimClear AI — Demo Video Generation Prompt

Use the following prompt with **Google Gemini** (or similar AI video generation tool) to create a professional demo video of ClaimClear AI.

---

## Gemini Video Generation Prompt

```
Create a 60-90 second professional product demo video for "ClaimClear AI", an
AI-powered insurance claim explanation assistant. The video should have a modern,
clean corporate aesthetic with a blue-to-teal gradient color scheme.

VIDEO STRUCTURE:

SCENE 1 (0-10s) — Opening
- Animated logo reveal: a shield icon with "ClaimClear AI" text
- Tagline fades in: "Making insurance decisions crystal clear"
- Background: subtle gradient from deep navy (#0f4c81) to teal (#17a2b8)
- Soft, professional background music

SCENE 2 (10-20s) — The Problem
- Split screen showing:
  - Left side: A frustrated customer reading a dense insurance letter full of
    jargon, with highlighted complex terms like "subrogation", "deductible
    aggregate", "exclusionary clause"
  - Right side: A customer service representative on the phone, looking
    overwhelmed with a long queue
- Text overlay: "Complex claim decisions → Confused customers → Costly support calls"

SCENE 3 (20-40s) — The Solution Demo (Streamlit UI)
- Screen recording style showing the ClaimClear AI Streamlit interface:
  1. User selects "Denied Health Claim" from sample dropdown
  2. Form auto-fills with: Claim ID "CLM-2024-78432", Customer "Sarah Johnson",
     Health policy, $3,200 claim amount
  3. Decision reason shows: "Out-of-network provider"
  4. User clicks the blue "Generate Explanation" button
  5. Loading spinner appears briefly
  6. Clear, friendly explanation appears in a light blue card
  7. Show the metrics: Comprehension Score 8.5/10, Time Saved ~12 min
  8. Show the glossary section with defined terms

SCENE 4 (40-55s) — The Pro Version
- Transition to the React + Rust interface showing:
  1. Modern, beautiful UI with gradient header
  2. Same claim being processed
  3. Emphasize the speed (< 1 second response)
  4. Show the circular comprehension score gauge
  5. Show expandable glossary accordion

SCENE 5 (55-70s) — Key Metrics & Benefits
- Animated statistics appearing one by one:
  - "8.5/10 Customer Comprehension Score"
  - "12 min Average Time Saved per Claim"
  - "30% Reduction in Support Calls"
  - "< 5 seconds to Generate Explanation"
- Icons accompanying each metric

SCENE 6 (70-80s) — Architecture Flash
- Brief animated architecture diagram showing:
  Customer → UI → AI Engine (OpenAI GPT-4o) → Clear Explanation
- Two paths: "Prototype (Streamlit)" and "Production (Rust + React)"
- Emphasize: "Built for demo AND production"

SCENE 7 (80-90s) — Closing
- Return to gradient background
- Logo centered with tagline
- Text: "Built at the AI Prototype Challenge"
- "Powered by OpenAI GPT-4o"
- Fade to black

STYLE GUIDELINES:
- Color palette: Navy (#0f4c81), Teal (#17a2b8), White, Light blue (#f8fbff)
- Font: Clean sans-serif (Inter or similar)
- Transitions: Smooth fades and slides, no flashy effects
- Music: Upbeat but professional corporate background track
- Pace: Moderate, allowing viewers to read text overlays
- Aspect ratio: 16:9
- Resolution: 1080p
```

---

## Alternative: Slide-Based Video Prompt

If full video generation isn't available, use this prompt to generate slides that can be assembled into a video:

```
Create 7 professional presentation slides for a product demo of "ClaimClear AI",
an AI insurance claim explanation assistant.

Slide 1: Title — Logo, name, tagline on gradient background
Slide 2: Problem — Complex jargon, frustrated customers, costly support
Slide 3: Solution — Screenshot of Streamlit UI with sample explanation
Slide 4: Pro Version — Screenshot of React UI with modern design
Slide 5: How It Works — Simple 3-step flow diagram
Slide 6: Impact Metrics — 4 key statistics with icons
Slide 7: Closing — Logo, "Built at AI Prototype Challenge"

Use navy-to-teal gradient theme. Clean, modern corporate aesthetic.
```

---

## Screen Recording Guide (Manual Demo Video)

If creating a screen recording instead:

1. **Open the Streamlit app** in Chrome (clean browser, no bookmarks bar)
2. **Start recording** (OBS or Loom)
3. **Walk through**:
   - Show the empty form
   - Click "Load Sample Claim" (the denied health claim)
   - Point out the sidebar options (tone, reading level)
   - Click "Generate Explanation"
   - Scroll through the results
   - Highlight the comprehension score
   - Show the glossary
   - Click "Download Explanation"
4. **Narrate** or add voiceover explaining each step
5. **Keep it under 2 minutes**
