# Cross-verification record

This record documents a fresh end-to-end verification performed on
27 August 2026 before release v0.1.1. It is an internal cross-check of the
public proof and code, not independent reproduction or peer review by a third
party.

## Logical audit

The proof was compared with the definitions and reduction lemmas in Puleo's
paper and with Gupta's maximum-degree-seven preprint. The following points
were checked explicitly.

- Proper-subgraph minimality rules out reducible vertex and edge sets.
- Robustness makes every endpoint link used in the argument connected; the
  WKE lemma makes each such link non-WKE.
- A degree-eight link has eight vertices, and the eight-vertex census forces
  an incident edge of codegree at least four.
- The two-hub local graph contains exactly all triangles meeting either hub;
  omitted A--B and external edges do not affect the reduction criterion.
- The degree budget for a common neighbour is at most six after accounting
  for its two hub edges.
- The generalized template gives a valid Puleo certificate under its stated
  inequality.
- In both exceptional records, every exclusive vertex on the degree-eight
  side redirects to a codegree-four edge whose common-neighbour core is
  exactly K4-e. No unlisted ambient neighbour can alter that core.

No logical contradiction or missing case was found.

## Fresh computational results

The standalone optimizer-free certificate verifier reported:

```text
records 37174
verified_witnesses 37172
obstruction_indices [10708, 10709]
ALL SAVED CERTIFICATES VERIFIED WITHOUT AN OPTIMIZER
```

The template verifier reported 208 valid template certificates. The
eight-vertex maximum-degree-four census reproduced 1,929 connected unlabelled
graphs and exactly eight non-WKE graphs, with minimum possible maximum degree
four. The full eight-vertex pass reproduced 11,117 connected unlabelled
graphs and 443 connected non-WKE graphs.

The two exceptional records were independently encoded in Z3. Both were
unsatisfiable as two-hub reductions, and both redirected cores were verified
as K4-e.

The orbit catalogue and template catalogue were regenerated from scratch and
matched the released files byte for byte:

```text
74C38803093DA7BCEDB43A728E32D6AF73CF3314119E187160A093708A21D43A  tuza_delta8_mixed_pairs.json
76A40449347F4B63722F040CA482407B9DF1FB4BE7D4F4FAC88C52A4166B6152  tuza_delta8_template_certificates.json
```

The three certificate shards also matched the hashes recorded in
`REPRODUCIBILITY.md`.

## Verification of the degree-seven dependency

The complete verification suite from the repository accompanying Gupta's
arXiv:2608.06538 was rerun at commit
`bf8415fac44f4eeed6c0f7a2273b843d689b065e`. All four components passed:

- sharpness and anchor checks;
- the complete codegree-six template check;
- all 1,144 codegree-four certificate orbits and 18,304 cross-edge
  extensions;
- all 1,122,304 codegree-five boundary configurations.

## Conclusion and limitation

All released finite claims were reproduced, the logical reduction was checked
against the cited primary sources, and no defect was found. This substantially
raises confidence in the result, but it does not replace independent review by
another mathematician or an independently written implementation.
