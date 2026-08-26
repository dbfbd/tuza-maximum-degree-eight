# Reproducing the maximum-degree-eight Tuza computation

This directory contains the finite verification supporting Yang Xu's preprint
*Tuza's conjecture for graphs of maximum degree at most eight*.

The calculation was completed on 27 August 2026 with:

- Python 3.13.2;
- NumPy 2.3.1;
- SciPy 1.16.2 (`scipy.optimize.milp`);
- Z3 5.1.0 from `work/vendor`;
- nauty 2.9.0 (`work/nauty/geng.exe`).

The proof also uses Gupta's maximum-degree-seven result.  The locally tested
repository snapshot is commit
`bf8415fac44f4eeed6c0f7a2273b843d689b065e` in
`work/tuza-maximum-degree-seven`.

## Fast verification of saved certificates

Run from the workspace root:

```powershell
python work/tuza_delta8_certificate_verify.py `
  work/tuza_delta8_cert_shard0.json `
  work/tuza_delta8_cert_shard1.json `
  work/tuza_delta8_cert_shard2.json

python work/tuza_delta8_template_verify.py `
  work/tuza_delta8_template_certificates.json

python work/tuza_delta8_obstruction_verify.py
python work/tuza_delta8_link_census.py
```

Expected headline output:

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

The two optimizer-free verifiers use only exact integer and set operations.
Z3 is used only for the independent unsatisfiability check of the two local
exceptions.

## Regenerating the orbit catalogue

```powershell
python work/tuza_delta8_mixed_pairs.py `
  --output work/tuza_delta8_mixed_pairs_regenerated.json `
  --template-output work/tuza_delta8_template_certificates_regenerated.json
```

The regenerated pair catalogue must contain 37,174 records and be bytewise
identical to `tuza_delta8_mixed_pairs.json`.

## Regenerating all unrestricted certificates

The following three commands are independent and may run in parallel:

```powershell
python work/tuza_delta8_mixed_worker.py --shards 3 --shard 0 `
  --save-witnesses --output work/tuza_delta8_cert_shard0_regenerated.json
python work/tuza_delta8_mixed_worker.py --shards 3 --shard 1 `
  --save-witnesses --output work/tuza_delta8_cert_shard1_regenerated.json
python work/tuza_delta8_mixed_worker.py --shards 3 --shard 2 `
  --save-witnesses --output work/tuza_delta8_cert_shard2_regenerated.json
```

Then pass the three regenerated files to
`tuza_delta8_certificate_verify.py`.  MILP may choose different valid
certificates on another solver version, so regenerated certificate files need
not be bytewise identical; the independent verifier's acceptance is the
relevant test.

## SHA-256 of the verified artefacts

```text
74C38803093DA7BCEDB43A728E32D6AF73CF3314119E187160A093708A21D43A  tuza_delta8_mixed_pairs.json
76A40449347F4B63722F040CA482407B9DF1FB4BE7D4F4FAC88C52A4166B6152  tuza_delta8_template_certificates.json
7849B89A31D91B45BAFB2E6C6F9E457D30F8BF14E9AEA11FB5F04DF053B8A7C5  tuza_delta8_cert_shard0.json
43257C7F60E7FB68E2E3F2AA5A063186D73946DD9D6B740283CCB80F2D854A86  tuza_delta8_cert_shard1.json
6FD12232A7D60BFCC8D7863E7F546BCED6071C1761389EE6BB9723CEB109A66E  tuza_delta8_cert_shard2.json
```

## Scope of the computation

The catalogue covers every compatible local graph around an edge `uv` where
`deg(u)=8`, both endpoint links are connected and non-WKE, and the triangle
codegree is between four and seven.  The other endpoint has every possible
degree from five through eight.  Necessary degree constraints are imposed,
but no sufficiency assumption about embedding the local graph in an ambient
graph is used; consequently the catalogue may overcount, which is safe.

This material has passed the released exact verifiers but has not yet been
independently reproduced or peer reviewed.
