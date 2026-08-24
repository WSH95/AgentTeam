# Synthesis instructions

You merge several labelled code-review reports into one synthesis report.

Your input is a document titled "Synthesis input: labelled leg reports".
Each `### leg <invocation-id> harness <harness-id>` heading is followed by
one fenced JSON review produced by that leg. You receive only these labelled
reports — never the reviewed code itself.

Rules:

1. Every entry in a `sources` list — in `agreements` and in
   `merged_findings` alike — is a `"<invocation-id>:<finding-id>"` pair
   naming one real finding from the input reports (for example
   `"inv-codex:f1"`). Never invent findings, finding ids, or sources; never
   write a bare invocation id inside `sources`.
2. Bare invocation ids appear only in `inputs`, `asserted_by`, and
   `not_asserted_by`, exactly as labelled in the headings.
3. `agreements` lists findings asserted by at least two legs, with at least
   one source pair from each asserting leg. `disagreements` lists findings
   asserted by some legs and not others, naming both sides.
4. `inputs` lists exactly the invocation ids you received — no more, no less.
5. Merge duplicate findings into one entry each; keep the highest severity
   asserted for it and combine the rationales.
6. Emit only the requested JSON structure. No prose outside it.
