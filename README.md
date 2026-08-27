# Tuza's conjecture for graphs of maximum degree at most eight

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22124333.svg)](https://doi.org/10.5281/zenodo.22124333)

This repository accompanies Yang Xu's computer-assisted preprint proving
Tuza's triangle packing-covering conjecture for every graph of maximum degree
at most eight.

For a graph `G`, let `nu(G)` be the maximum number of pairwise edge-disjoint
triangles and let `tau(G)` be the minimum number of edges meeting every
triangle.  The claimed theorem is

```text
Delta(G) <= 8  ==>  tau(G) <= 2 nu(G).
```

The argument extends Anish Gupta's recent maximum-degree-seven theorem
(arXiv:2608.06538) using Puleo's reducible-set framework.  Its finite part
contains:

- 37,174 compatible local-graph orbits after template reduction;
- 37,172 explicit positive reducibility certificates;
- 208 generalized-template certificates;
- two exceptional local graphs, independently confirmed with Z3 and
  eliminated by redirecting the selected edge to a `K4-e` core.

All positive certificates have passed standalone verifiers that use only
exact integer and set operations.  The full orbit catalogue was regenerated
byte for byte.  A fresh end-to-end cross-check, including the complete
verification suite for the maximum-degree-seven dependency, is recorded in
[`AUDIT.md`](AUDIT.md).

## Paper

The current preprint is [`paper/tuza_maximum_degree_eight.pdf`](paper/tuza_maximum_degree_eight.pdf).
It has not been peer reviewed or independently reproduced.

## Quick verification

Install the Python dependencies:

```console
python -m pip install -r requirements.txt
```

Then run:

```console
python work/tuza_delta8_certificate_verify.py work/tuza_delta8_cert_shard0.json work/tuza_delta8_cert_shard1.json work/tuza_delta8_cert_shard2.json
python work/tuza_delta8_template_verify.py work/tuza_delta8_template_certificates.json
python work/tuza_delta8_obstruction_verify.py
python work/tuza_delta8_link_census.py
```

Expected headline results:

```text
records 37174
verified_witnesses 37172
obstruction_indices [10708, 10709]
ALL SAVED CERTIFICATES VERIFIED WITHOUT AN OPTIMIZER
verified_template_certificates 208
ALL TEMPLATE CERTIFICATES VERIFIED WITHOUT AN OPTIMIZER
ALL TWO OBSTRUCTIONS AND REDIRECTIONS VERIFIED
connected_non_WKE 8
minimum_possible_max_degree 4
```

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the complete environment,
regeneration commands, and SHA-256 checksums.

## Software and data

The verification code is released under the MIT License.  The paper and proof
outline are released under CC BY 4.0.  The included `geng.exe` was built from
nauty 2.9.0; nauty's copyright notice is retained in `work/nauty/COPYRIGHT`.

Computational exploration and manuscript preparation were assisted by OpenAI
Codex.  Exact certificates and standalone verifiers are released so that the
finite claims do not depend on trusting a language model or an optimizer.

## Citation

The archival release is available at
[doi:10.5281/zenodo.22124333](https://doi.org/10.5281/zenodo.22124333).
Cite it as:

> Yang Xu, "Tuza's conjecture for graphs of maximum degree at most eight,"
> computer-assisted preprint and verification archive, version 0.1.2, 2026.
