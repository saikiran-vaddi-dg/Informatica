# HHS_SDE_ORA_USE_Bank_Dimension_ORA

Hardcoded-for-testing copy of
[HHS_SDE_ORA_BankDimension](../HHS_SDE_ORA_BankDimension/index.md) with its
three `$$` mapping parameters (`$$LAST_EXTRACT_DATE`, `$$DATASOURCE_NUM_ID`,
`$$TENANT_ID`) replaced by literals (`2020-01-01`, `601`, `'DEFAULT'`), so the
same bank/branch/account extraction into `W_BANK_DS` can be validated without
resolving environment/session config.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
