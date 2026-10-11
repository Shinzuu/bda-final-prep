<context>
This is my CSE 4345 Big Data Analytics final-exam guide. The exam is on 13 October 2026, 2 days from now.
- Live site: https://shinzuu.github.io/bda-final-prep/
- Source: ~/Documents/study/bda-final-prep/. `python3 build.py` turns cards/w05..w10.json and diagrams/*.svg
  into one self-contained index.html plus two PDFs.
- What's in it: the teacher said the exam comes from the end-of-chapter question pools, so every week has
  its 126 pool questions answered at exam length, 36 topic cards, 330 drill questions, a mock paper and a
  formula sheet. All answers have been checked twice against the slides.

I revise on my phone and laptop. The guide feels like too much studying: 192 phone screens, and every visit
starts from zero. I want it to feel light and doable without losing any content.

An audit of the current site found:
1. Each week runs about 28 phone screens, and each card about 3.7.
2. The top bar hides W10, Mock, Sheet, All answers and Theme off-screen on a phone.
3. There is no progress tracking; only the theme is saved.
4. There is no navigation inside a week, and no link from a pool question to its card.
5. Diagram text is 5–6 px on a phone.
6. Content repeats: the sheet's one-liners equal the cards' 1-mark answers, and 6 diagrams appear twice.
7. Cards are one long block, so traps and scenario answers arrive 3–4 screens in.
8. Pool, drill and mock questions use the same box style.
9. The mock's i–iv parts run together on one line.
10. The formula table is unreadable on a phone.
</context>

<task>
Redesign how the guide presents and paces its content, so a session feels short and finishable and the
whole guide feels manageable. Then rebuild it, verify it, and deploy it.
</task>

<requirements>
1. **Keep all content.** Every pool question and answer, card layer, drill, mock part and formula stays
   reachable. You may change order, grouping and what is folded by default. Remove only true duplicates,
   and keep each removed copy available as a link to the original.
2. **Study path.** Add a "Start here" plan for the 2 days left. Break it into sessions of about 20 minutes,
   each labelled with a time estimate and its scope (for example "Week 7 pool, 18 min"), ordered by exam
   yield: pool questions first, then each card's traps and scenarios, then drills.
3. **Progress.** Each pool question and drill gets Known / Again marks, and each card gets a "done" tick.
   Show a progress bar per week and overall. Save it in localStorage, wrapped in try/catch so the page
   still works without it, and add a reset button.
4. **Focus mode.** Add a flashcard view that shows one question at a time for any week or session: tap to
   reveal, mark Known or Again, and Again items return later in the session.
5. **Answer first.** Show each topic's one-line answer up front. Put the layers in this order, most
   exam-useful first: one-liner, traps, scenario table, facts, how it works, why, compare, maths. Fold
   everything after the scenario table by default.
6. **Navigation.**
   - On a phone, the top bar shows every control without sideways scrolling. A bottom tab bar or a menu
     are both fine.
   - Add an in-week contents list.
   - Each pool question links to its card, and each card links back to its pool questions.
   - Add back-to-top.
   - The page remembers your place.
7. **Fix the audit's problems:**
   - diagram text is 11 px or more on a 390 px phone, by simplifying or allowing horizontal pan per figure;
   - diagrams are capped at about 60% of the viewport height on desktop;
   - pool, drill and mock questions each get a distinct style;
   - the mock's i–iv parts sit on separate lines;
   - the formula sheet becomes stacked cards on a phone.
8. **PDF.** Keep the two PDFs, and make the full one smaller by printing the exam-useful layers only.
</requirements>

<decisions>
Already decided:
- One self-contained HTML file with no external libraries.
- Content stays at full depth; the slides remain the source of truth.
- The amber BDA palette and colour code stay: yellow = answer, red = trap, blue = maths.
- Dark mode stays.
- The existing pool answers and their wording are verified, so don't rewrite them.

Your call:
- Visual design details, within the palette.
- How sessions are split, as long as each is about 15–25 minutes.
- Whether focus mode is a separate view or an overlay.

Ask me before:
- deleting any content;
- changing any answer text;
- adding any external dependency;
- pushing to GitHub before I have seen screenshots.
</decisions>

<verification>
Before reporting done:
- Run `node test_layout.mjs` and get no overflow at 390 px or 1366 px.
- Screenshot the following on a phone:
  - Start here;
  - one week's pool;
  - a card;
  - focus mode;
  - the sheet.
- Confirm by script that the counts of pool questions, cards, drills, mock parts and formulas equal the
  current build's (126 / 36 / 330 / 24 / 52).
- Confirm that progress survives a reload.
- Give the new page length in phone screens, with all answers folded, against 192 now.
</verification>

<output>
Report:
- what changed, as at most 8 bullets;
- the screenshots;
- the before/after numbers.

Then wait for my go-ahead before pushing.
</output>
