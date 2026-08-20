# HHS_SDE_ORA_QuickDemoFact

Single-mapping, 4-column read of `FV_GTAS_ACTIVITY_BALANCES` (rounding `AMOUNT` to 2 decimal places) into the same shared target table, `W_GTAS_ACTIVITY_BALANCES_FS`, that the full production `HHS_SDE_ORA_GTASActivityBalanceFact` workflow loads at a 9-column composite grain — see [hrd_mapping.md](hrd_mapping.md#known-caveats) for why this looks like a demo/tutorial artifact rather than a real ETL load.

- [Workflow logic (Description, Key Columns)](extraction.md)
- [Test cases, dataflows & caveats](hrd_mapping.md)
