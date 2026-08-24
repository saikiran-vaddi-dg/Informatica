# HHS_SDE_ORA_BankDimension

SDE mapping extracting bank/branch/account data from Oracle EBS (internal
`CE_BANK_ACCOUNTS` union external `IBY_EXT_BANK_ACCOUNTS`/`IBY_ACCOUNT_OWNERS`,
joined to a derived branch view and a primary-contact lookup) into staging
table `W_BANK_DS`, deduplicated on a derived `INTEGRATION_ID`.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
