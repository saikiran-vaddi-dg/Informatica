# HHS_SDE_ORA_GTASActivityBalanceFact

SDE mapping extracting GTAS activity-balance journal-line detail from Oracle
EBS Federal Financials (`FV_GTAS_ACTIVITY_BALANCES`, incrementally filtered
on `CREATION_DATE`) into staging table `W_GTAS_ACTIVITY_BALANCES_FS`, with a
conditional (nested IIF) lookup deriving `PROVIDER_RECIPNT_NAME` from either
`LKP_PROVD_RECP` or `LKP_INTRA_HHS_ELI` depending on the shape of
`PROVIDER_RECIPNT_ID`.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
