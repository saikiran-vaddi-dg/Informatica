# HHS_SDE_ORA_BankDimension

* [Extraction](extraction.md) - Straight SDE extract-to-staging load of CEBV_BANK_ACCOUNTS into W_BANK_DS; test case reviewed and confirmed, dataflow not yet built.
* [HRD Mapping](hrd_mapping.md) - Column-by-column derivation from the Informatica workflow's transformation logic to each W_BANK_DS target column, as encoded in the HRD test case's JDBC 2 (expected) recompute query.
* Computation Contract - not yet created; dataflow not built (`dataops_mcp` unauthenticated)
