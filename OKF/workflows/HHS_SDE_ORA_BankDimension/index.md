# HHS_SDE_ORA_BankDimension

SDE-layer Oracle EBS bank/account/branch extract (`HZ_PARTIES`, `CEBV_BANK_ACCOUNTS`, `CEBV_BANK_BRANCHES`) via the reusable mapplets `HHS_mplt_BC_ORA_BankDimension`/`HHS_mplt_SA_ORA_BankDimension`, into staging table `W_BANK_DS`.

- [Workflow logic (Description, Key Columns)](extraction.md)
- [Test cases, dataflows & caveats](hrd_mapping.md)
