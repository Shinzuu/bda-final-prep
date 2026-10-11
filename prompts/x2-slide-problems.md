<task>
Build the slide-problem bank: every worked example, calculation, numeric claim and exercise on the slides,
each turned into exam-shaped one-step drills. The teacher said solving the slide exercises covers the
paper, and in the last final the slide examples came back almost verbatim.
</task>

<requirements>
1. Find every number-bearing example on the slides. Examples:
   - 97% I/O reduction, 33× speedup, containers per queue;
   - iterations × data size disk I/O, GraySort ratios;
   - map-side aggregation 250,000×, partition pruning 3/73,000, `hash % N` buckets;
   - Kafka throughput and partition math, Lambda vs Kappa costs;
   - lie factor, data-ink, hexbin and cube reduction;
   - 3-hop reach, 40× speedup, IQR threshold, genomics storage.

   Also take every Analytical question and every Live Exercise.
2. For each example, write:
   - the slide's own numbers and full worked solution, with every number recomputed by `python3 -c`;
   - 2 one-step variants in the DM-final shape: a scenario with the earlier steps given and ONE step asked;
   - one "explain why" follow-up of the kind that went with each calculation in the last final.
3. Rank each example: "very likely" if it is a slide worked example with explicit numbers; "likely" if it
   is a numeric claim on a slide.
</requirements>

<output>
Write `~/Documents/study/bda-final-prep/extra/slide_problems.json` as
`[{id, week, slides, title, given, solution_steps:[...], answer, variants:[{q, a}], why:{q, a}, rank}]`,
valid JSON. Reply with a count per week, plus any slide number that does not recompute.
</output>
