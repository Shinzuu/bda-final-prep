<context>
This is the BDA final guide, live at https://shinzuu.github.io/bda-final-prep/. The source is
`~/Documents/study/bda-final-prep/`: `build.py` turns cards/*.json, extra/{comparisons,slide_problems,predicted}.json
and diagrams/ into `index.html`.

The exam is on 13 October 2026, about one day away, and the student studies on a phone. The teacher says
the slides are everything, and that the slide exercises and problem solving cover the paper. The real paper
format, based on the same department's Data Mining final, is scenario questions with short i–iv parts,
"distinguish / why / identify", and one-step calculations.

All the content is verified. The problem is shape and volume. The site has many views (plan, weeks,
comparisons, problems, mock, sheet) and reads as too much.

The student wants:
- ONE checklist to work down;
- chapter by chapter;
- in each chapter, learn, then practise, then test;
- when the last item is ticked, preparation is done;
- only what they could actually write in the exam, with nothing verbose.
</context>

<task>
Rebuild the site around a single linear checklist, Week 5 → Week 10, in which every item is short and exam-writable. Then rebuild and verify. Don't push.
</task>

<requirements>
1. **One checklist is the main view.** Six chapters in order, W5 to W10, then a final "Exam morning"
   section. Each chapter has three steps, each a group of tickable items:
   - **Learn:** the chapter's topics, each reduced to what you'd write.
     - The one-line definition.
     - Up to 3 key points.
     - Traps.
     - The diagram, if the exam might ask you to draw it.
     - The comparisons rated high-likelihood for that chapter, as a 3–4 row table plus the key difference.
   - **Practise:** the chapter's slide worked examples (extra/slide_problems.json, the "very likely" items
     first). Each shows the givens, then the solution on tap, then one one-step variant.
   - **Test:** the chapter's exam questions (cards pool), done flashcard-style, then that chapter's question
     from the predicted papers in extra/predicted.json.

   A progress bar shows per chapter and overall. Ticking the final item shows "Preparation complete".
2. **Exam-writable only.** On the main path, show only content a student would write in the paper:
   definitions, lists, steps, comparisons, formulas with one worked line, traps, and model answers at exam
   length.
   - Cut narrative, history, repeated explanations, and long 5-mark essays, keeping their skeletons as
     bullets.
   - Anything cut moves into a single "More detail" fold or an archive view. Don't delete it from the JSON;
     only change what the checklist shows.
   - Target: each chapter readable in about 60–80 minutes, and the whole checklist in about 8 hours.
3. **Short wording.** Answers stay as verified. Interface text is plain and brief: "Learn", "Practise",
   "Test", "Got it", "Review again". Item titles name the topic. Don't use ids, jargon badges or
   upper-case micro-labels.
4. **Phone first.** 17px body text, generous spacing, comparison tables as stacked rows, each item a
   compact row that expands on tap. The rest of the site (weeks, comparisons, problems, mock, sheet,
   focus mode, PDFs) stays reachable from one small menu as reference, but the checklist is the home
   screen.
5. **Progress carries over.** Keep the existing localStorage key and stored values. Map existing marks
   (pool Known, card done, block ticks) onto checklist items, so ticks the student already made still
   show as ticked.
</requirements>

<decisions>
Already decided:
- Chapter order is W5 → W10. That replaces the emphasis-ordered day plan, which can stay as a reference.
- Slides are the source.
- Verified answers are not rewritten.
- One self-contained HTML file; keep the palette and dark mode.

Your call:
- Which bullets count as "key points", taken from the card's facts and why layers, at most 3.
- How long items are split.

Ask me before: deleting any JSON content.
</decisions>

<verification>
- `node test_layout.mjs` shows no overflow at 390 and 1366.
- A script reports: items per chapter, estimated minutes per chapter (about 200 words a minute reading, plus
  2 minutes per practice item), and that every pool question and every high-likelihood comparison appears
  somewhere in the checklist.
- Pre-seed localStorage in the current format and confirm the existing ticks show.
- Phone screenshots of the checklist top, one chapter's Learn, Practise and Test steps, and the completion
  state go to /tmp/claude-1000/v6shots/.
- Run heavy commands with `nice -n 15`, and kill any headless Chrome you start.
</verification>

<output>
Report:
- what changed, in at most 6 bullets;
- the per-chapter item counts and minutes;
- the screenshot paths;
- confirmation that progress survives.

Don't commit or push.
</output>
