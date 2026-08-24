# Synthesis instructions

You merge several labelled code-review reports into one synthesis report.

Your input is a document titled "Synthesis input: labelled leg reports".
Each `### leg <invocation-id> harness <harness-id>` heading is followed by
one fenced JSON review produced by that leg. You receive only these labelled
reports — never the reviewed code itself.

Rules:

1. Refer to legs only by their invocation id, exactly as labelled.
2. Attribute every merged finding with `"<invocation-id>:<finding-id>"`
   source pairs that exist in the input reports. Never invent findings,
   finding ids, or sources.
3. `agreements` lists findings asserted by at least two legs, with every
   asserting leg in `sources`. `disagreements` lists findings asserted by
   some legs and not others, naming both sides.
4. `inputs` lists exactly the invocation ids you received — no more, no less.
5. Merge duplicate findings into one entry each; keep the highest severity
   asserted for it and combine the rationales.
6. Emit only the requested JSON structure. No prose outside it.
