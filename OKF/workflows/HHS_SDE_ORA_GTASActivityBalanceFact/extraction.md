# HHS_SDE_ORA_GTASActivityBalanceFact — Workflow Logic

## Description

Single-mapping workflow `HHS_SDE_ORA_GTASActivityBalanceFact`: source `FV_GTAS_ACTIVITY_BALANCES` (Oracle, `FDABI` schema) flows through `SQ_FV_GTAS_ACTIVITY_BALANCES` -> `EXP_GTASACTIVITY` -> target `W_GTAS_ACTIVITY_BALANCES_FS`. The source qualifier applies an incremental filter on `CREATION_DATE` using mapping variable `$$LAST_EXTRACT_DATE`. Of 43 target columns, 38 are straight passthrough; 4 are computed:

- `PROVIDER_RECIPNT_ID` = source `PARENT_AWARD_ID` reused under a different alias.
- `PROVIDER_RECIPNT_NAME` = nested `IIF`: if `LENGTH(id)=7` and `SUBSTR(id,1,3)!='075'` -> `LKP_PROVD_RECP(SUBSTR(id,2,2))`; elif `SUBSTR(id,1,3)='075'` -> `LKP_INTRA_HHS_ELI(SUBSTR(id,4,4))`; else -> `LKP_PROVD_RECP(id)`. `LKP_PROVD_RECP` queries `FND_FLEX_VALUES_VL` (`VALUE_CATEGORY='HHS_TP_ELIMINATION_CODE'`) matched on `FLEX_VALUE`. `LKP_INTRA_HHS_ELI` looks up `W_GTAS_INTRAHHS_D` on `TP_MAIN_ACT`, returning `OPDIV`.
- `DATASOURCE_NUM_ID` = mapping variable `$$DATASOURCE_NUM_ID` (unresolved runtime parameter).
- `INTEGRATION_ID` (`out_INTEGRATION_ID`) — the `EXPRESSION` attribute is empty in the XML, so it resolves to `NULL` for every row. This is the mapping's actual current behavior (a likely gap), not a guessed intended rule. **Confirmed stale against production** — see [hrd_mapping.md](hrd_mapping.md#known-caveats).

## Key Columns

- **Unique/natural key (inferred from fact grain, not a declared `KEYTYPE` in the XML — no target field declares anything other than "NOT A KEY")**: `CCID`, `PERIOD_NUM`, `SET_OF_BOOKS_ID`, `JE_HEADER_ID`, `JE_LINE_NUM`, `AE_HEADER_ID`, `AE_LINE_NUM`, `BALANCE_TYPE`, `RECORD_CATEGORY`.
- **Derived / lookup-dependent**: `PROVIDER_RECIPNT_ID` (aliased from `PARENT_AWARD_ID`), `PROVIDER_RECIPNT_NAME` (nested lookup via `LKP_PROVD_RECP` / `LKP_INTRA_HHS_ELI`, branching on `PARENT_AWARD_ID` shape). **Confirmed stale against production** — see [hrd_mapping.md](hrd_mapping.md#known-caveats).
- **Parameterized (mapping variables, unresolved at design time)**: `DATASOURCE_NUM_ID` (`$$DATASOURCE_NUM_ID`), source qualifier incremental filter on `CREATION_DATE` (`$$LAST_EXTRACT_DATE`).
- **Known gap, not a lookup**: `INTEGRATION_ID` — empty `EXPRESSION`, always `NULL` per the XML (but not in production — see caveats).
