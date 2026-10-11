<context>
This is the BDA final guide in `~/Documents/study/bda-final-prep/`. The exam is on 13 October 2026, and the
student has about one day left.

`build.py` was just redesigned and is uncommitted; `git diff ed85b29` shows it. The redesign added
separate views (Start here, Weeks, Focus, Mock, Sheet), progress tracking, focus mode, and answer-first
cards. The original design brief is `prompts/improve-site-v1.md`.

Three new slide-based banks are now in `extra/`:
- `predicted.json`:
  - teacher-emphasis ranking per topic, with evidence;
  - two predicted 40-mark papers in the DM-final shape (scenario + i–iv, one calculation step);
  - a one-day plan of 16 blocks, 490 min, plus exam morning; its links use `card:wNN/<id>`,
    `pool:WN D1`, `cmp:<topic>` and `prob:<topic>`;
  - a must-know list of 40 items;
  - a skip list.
- `comparisons.json`: 82 "X vs Y" pairs. Each has a table, a key difference, a scenario cue, a likelihood
  rating and a card_id.
- `slide_problems.json`: 69 slide worked examples. Each has the solution steps, 2 one-step variants, a
  "why" question, a rank and a card field.

The teacher said everything examinable is on the slides, and solving the slide exercises covers the paper.
</context>

<task>
Fold the three banks into the redesigned site. The one-day plan becomes the main path, so the student opens
the site and knows exactly what to do next for the day. Then rebuild and verify.
</task>

<requirements>
1. **Start here.** It now leads with the one-day plan from predicted.json, replacing the generic
   34-session plan.
   - Each block shows its minutes, its task, and tappable links that resolve to the right card, pool
     question, comparison or slide problem.
   - Resolve `cmp:<topic>` and `prob:<topic>` links by matching topics. Every link must land somewhere;
     report any that can't.
   - Keep the "Next up" box, and block-level progress ticks.
2. **Comparisons view.** Add a view, filterable by week and by likelihood, with "high" items first. Each
   pair shows its table, key difference and cue. Each card links to its comparisons. Focus mode can flash
   comparisons, showing "X vs Y?" and revealing the key difference.
3. **Slide problems view.** Add a view, filterable by week and rank. Each problem shows the given numbers,
   with the solution steps folded behind a tap. The variants and the "why" question work as practice items
   with Known / Again marks. Focus mode supports them.
4. **Predicted papers.** Show them as two more papers in the Mock view, with the `why` evidence visible.
   Label them clearly as predictions.
5. **Must-know list.** Make it the top section of the Sheet view, as a one-screen checklist. Put the skip
   list in a folded "if short on time" note.
6. **Honesty.** Show the predictions' evidence, and keep the note that the plan still covers all 6 weeks.
7. **Keep everything else intact.** The existing content counts stay at 126 / 36 / 330 / 24 / 52. The
   existing progress keys in localStorage stay compatible.
</requirements>

<decisions>
Already decided:
- One self-contained HTML file.
- The palette and colour code.
- No pushing; the team lead reviews.
- The JSON content is not rewritten. A separate checker is fixing any errors in it now, so rebuild from
  the JSON at the end.

Your call:
- The navigation placement of the two new views, within the bottom tab bar's limits. A "More" menu is
  fine.
</decisions>

<verification>
- `node test_layout.mjs` reports no overflow at 390 and 1366.
- A script confirms every plan link resolves, and all 82 comparisons and 69 problems are rendered.
- Phone screenshots of Start here, Comparisons, Slide problems, a predicted paper and the Sheet go to
  /tmp/claude-1000/v4shots/.
- Kill any headless Chrome you start. Run heavy commands with `nice -n 15`.
</verification>

<output>
Report:
- what changed, in at most 8 bullets;
- the new page length in phone screens;
- the screenshot paths;
- any unresolved links.

Don't commit or push.
</output>
