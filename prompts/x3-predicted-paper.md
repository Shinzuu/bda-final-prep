<task>
Predict the final paper and write a one-day study plan from that prediction.
</task>

<requirements>
1. **Measure teacher emphasis per topic from the slides.** Use:
   - the number of slides on the topic;
   - "Key takeaways", "Lessons learned" and "Why it matters" boxes;
   - case-study slides;
   - a topic appearing in both Part 1 and Part 2;
   - topics in the Student Assessment Pool;
   - figures the teacher drew.

   Produce a ranked topic list per week with the evidence.
2. **Write two predicted papers** in the DM-final shape. Each has 40 marks: one 10-mark question per chapter
   for the 4 most likely chapters, plus OR options covering the other 2. Each part is a 2–3 line scenario
   followed by i–iv sub-questions, one of them a single calculation step built from a slide example. Give a
   model answer for every part, at the length its marks need.
3. **Write a one-day plan**, about 8 hours plus the exam morning. Use 25–40 minute blocks ordered by
   expected marks per minute. Each block names exactly what to do, linking card ids, pool question
   numbers, comparison ids from extra/comparisons.json, and slide-problem ids from
   extra/slide_problems.json. Those two files are being written right now by other workers, so refer to
   them by topic if the ids aren't there yet.

   Then add a "must-know list" of at most 40 items that fits on one screen, and a "skip if short on time"
   list.
4. **Be honest about uncertainty.** Every prediction carries its evidence, and the plan still covers all 6
   weeks at least lightly. The last final punished narrow prediction.
</requirements>

<output>
Write `~/Documents/study/bda-final-prep/extra/predicted.json` as
`{emphasis:[{week, topic, score, evidence}], papers:[{name, questions:[{q, week, parts:[{label, marks,
scenario, subs:[{q, a}]}], or:[...]}]}], plan:[{block, minutes, task, links:[...]}], must_know:[...],
skip:[...]}`, valid JSON. Reply with the top 10 topics and the plan outline.
</output>
