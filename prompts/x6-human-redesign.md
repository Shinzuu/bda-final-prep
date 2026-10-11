<context>
This is the BDA final guide, live at https://shinzuu.github.io/bda-final-prep/. The source is
`~/Documents/study/bda-final-prep/`: `build.py` builds `index.html` from cards/*.json, extra/*.json and
diagrams/.

The exam is on 13 October 2026, and the student is studying on this site right now, mostly on a phone. The
content is complete and verified. The student says it still isn't designed for human consumption. It reads
like a database dump: jargon labels, dense blocks, too many badges and buttons at once.

Specific problems in the current screens:
- Jargon labels. "POOL", "CARD", "VS" and "CALC" chips, "pool W6 D1", "MCQ Q2", card ids like "rdd,
  lazy-eval" inside plan text, "Known / Again", "drills".
- Plan blocks are walls of text with 8–10 chips each.
- Upper-case micro-labels everywhere.
- Comparison tables are cramped 3-column grids on a phone, and the Comparisons view runs 101 phone screens.
- The page heads pile counts on top of each other: "1/82 known", "Showing 82", "16 blocks · 8 h 10 min".

Load the `frontend-design` skill and follow it. Load `no-ai-slop` for all copy.
</context>

<task>
Redesign the presentation and the wording so the site reads like a calm, friendly study companion made by
a person. Keep all the content and features. Then rebuild and verify. Don't push.
</task>

<requirements>
1. **Plain language everywhere in the interface.**
   - Pool → "Exam questions"; cards → "Topics"; drills → "Practice"; VS → "Compare"; CALC → "Worked
     example"; Known / Again → "Got it" / "Review again".
   - Question references read naturally, for example "Week 6 exam question D1 (descriptive)".
   - Rewrite each plan block's task text into 1–3 short, human sentences that name topics by title, never
     by id. This copy lives in extra/predicted.json `plan[].task`. You may rewrite that field only, keeping
     its meaning.
2. **One clear next step.** The opening screen shows a greeting with days left, today's progress in one
   line, and one big "Continue: <block title> (35 min)" button. Everything else sits below and stays calm.
3. **Plan blocks.** Each block shows a title, minutes, the short task text, then a tidy list of what to
   open, grouped under quiet sub-labels (Read / Answer / Compare / Practise), as text links rather than a
   wall of chips. Show the full list on tap if it is long.
4. **Typography and space.** A readable body size (17px on a phone), line-height of about 1.6, fewer
   borders and boxes, more whitespace, sentence-case headings, and at most one accent colour per element.
   Keep the palette meaning: yellow = answer, red = trap, blue = maths.
5. **Phone tables.** Comparison and scenario tables become stacked "criterion → X / Y" rows on narrow
   screens. The Comparisons view shows high-likelihood pairs first, collapsed to title + key difference,
   with the table opening on tap, so the view scrolls fast.
6. **Fewer controls at once.** Filters become one compact row. Counts move into a single quiet progress
   line. Remove decorative badges that carry no meaning.
7. **Keep intact:**
   - all content and counts (126 / 36 / 330 / 24 / 52, 82 comparisons, 69 problems, both predicted papers);
   - focus mode, progress, the PDFs and dark mode;
   - the localStorage key and stored mark values exactly, because the student's progress must survive the
     update;
   - every answer and verified wording in cards/*.json and in the extra banks, apart from plan task text.
</requirements>

<verification>
- `node test_layout.mjs` shows no overflow at 390 and 1366.
- A script confirms the content counts and that every plan link still resolves.
- Load the page with localStorage pre-seeded from the current site's format, and confirm the progress shows
  correctly (no reset).
- Phone screenshots of the opening screen, a plan block, a topic, Compare, a worked example, focus mode and
  the Sheet go to /tmp/claude-1000/v5shots/, plus one desktop screenshot.
- Run heavy commands with `nice -n 15`, and kill any headless Chrome you start.
</verification>

<output>
Report:
- what changed, in at most 8 bullets;
- the screenshot paths;
- confirmation that progress survives.

Don't commit or push.
</output>
