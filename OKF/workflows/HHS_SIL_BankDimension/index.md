# HHS_SIL_BankDimension

SIL mapping that loads the `W_BANK_D` dimension from staging table
`W_BANK_DS`, classifying rows via a self-lookup on `W_BANK_D`, passing
through ~49 descriptive attribute columns unchanged, computing `DELETE_FLG`
from the row classification, and resolving `BANK_KEY_CODE` via a
master-code lookup.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
