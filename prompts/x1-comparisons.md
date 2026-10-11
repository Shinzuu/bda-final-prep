<task>
Build the comparison bank: every "X vs Y" the slides support, because "distinguish / compare" is the most
reliable question type.
</task>

<requirements>
1. Scan all 12 slide decks for every explicit comparison: tables with two or more columns of alternatives,
   "vs", "unlike", "compared to", "trade-off", before/after, old/new architecture, pros/cons.
2. Add the implicit pairs a teacher would naturally ask. Use only facts that appear on the slides, for
   example "Hive vs Presto latency", "narrow vs wide dependency", "Lambda vs Kappa", "partitioning vs
   bucketing", "row vs columnar", "data lake vs warehouse", "EARS-style vs ...".
3. For each comparison write:
   - the pair;
   - week and slide number(s);
   - a 4–6 row table (criterion | X | Y) with slide wording;
   - a one-sentence "the key difference" answer worth 2 marks;
   - one scenario cue ("if the question describes ..., the answer is X");
   - a likelihood tag: high if the slides show an explicit table or repeat it; medium if implicit.
4. Mark each pair as already covered in a card's contrasts (give the card id) or new.
</requirements>

<output>
Write `~/Documents/study/bda-final-prep/extra/comparisons.json` as
`[{id, week, slides, x, y, rows:[[criterion,x,y]], key, cue, likelihood, card_id|null}]`, valid JSON.
Reply with a count per week, plus the 10 pairs you rate most likely to be asked.
</output>
