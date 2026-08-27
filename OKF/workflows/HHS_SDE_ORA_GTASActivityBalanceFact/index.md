# HHS_SDE_ORA_GTASActivityBalanceFact

SDE mapping loading GTAS journal-line activity-balance detail from Oracle EBS
Federal Financials (`FV_GTAS_ACTIVITY_BALANCES`) into staging
`W_GTAS_ACTIVITY_BALANCES_FS`. Production logic actually lives in 4
session-level partition overrides (`_FDA`, `_PSC`, `_CDC`, `_IHS`) on
`SQ_FV_GTAS_ACTIVITY_BALANCES`, not the mapping-level default query — see
`extraction.md` for why. This test case covers the FDA session only.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
