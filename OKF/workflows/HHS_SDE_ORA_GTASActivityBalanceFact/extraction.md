---
generated:
  by: developer-agent
  at: "2026-08-27T16:31:45+05:30"
  commit: d0c33754e02b2ca174e339c8a05e51d310ab9b0e
---

# HHS_SDE_ORA_GTASActivityBalanceFact — Extraction

## Description

SDE mapping loading GTAS journal-line activity-balance detail from Oracle EBS
Federal Financials (`FV_GTAS_ACTIVITY_BALANCES`) into staging
`W_GTAS_ACTIVITY_BALANCES_FS`, via one Expression (`EXP_GTASACTIVITY`). The
mapping-level default `Sql Query` override (`CREATION_DATE >=
$$LAST_EXTRACT_DATE`) is dead code — it's missing 2 of the SQ's output ports
and is never what actually runs. Production instead uses 4 session-level
partition overrides on `SQ_FV_GTAS_ACTIVITY_BALANCES` (`_FDA`, `_PSC`, `_CDC`,
`_IHS`), each filtering `PERIOD_YEAR IN ($$GTAS_FISCAL_YR_<X>_EXT)` on a
distinct physical partition, and each computing `PROVIDER_RECIPNT_ID` via a
`CASE WHEN TRADING_PARTNER_TYPE = ...` expression joined to
`apps.HZ_CUST_ACCOUNTS`/`apps.AP_SUPPLIERS`/`apps.GL_JE_LINES` — not the
simple `PARENT_AWARD_ID` passthrough the base mapping implies. That value
then feeds `EXP_GTASACTIVITY`'s unchanged nested-IIF lookup chain
(`LKP_PROVD_RECP` keyed on `FND_FLEX_VALUES_VL` filtered to
`VALUE_CATEGORY='HHS_TP_ELIMINATION_CODE'`; `LKP_INTRA_HHS_ELI` keyed on
`W_GTAS_INTRAHHS_D.TP_MAIN_ACT`) to derive `PROVIDER_RECIPNT_NAME`.

## Key Columns

- No declared unique key — composite `CCID, PERIOD_NUM, SET_OF_BOOKS_ID,
  JE_HEADER_ID, JE_LINE_NUM, AE_HEADER_ID, AE_LINE_NUM` used as the
  DataCompare key.
- Session-override-derived: `PROVIDER_RECIPNT_ID` — computed per-session via
  `TRADING_PARTNER_TYPE`-branched joins; this test covers the FDA session
  only. PSC/CDC/IHS share identical join/CASE logic but different
  `$$GTAS_FISCAL_YR_<X>_EXT` filters and physical partitions — would need
  parallel test cases for full session coverage (gap, not yet covered).
- Conditional lookup: `PROVIDER_RECIPNT_NAME` — nested nature-of-ID branch on
  length/prefix of `PROVIDER_RECIPNT_ID`, against
  `LKP_PROVD_RECP`/`W_GTAS_INTRAHHS_D`.
- Unresolved param, left as literal placeholder: `$$GTAS_FISCAL_YR_FDA_EXT`
  in the expected query's WHERE (no default, no dataops.config.yaml
  override) — must be substituted with the fiscal year actually loaded into
  the target before this test is meaningful.
- Unresolved/ignored: `DATASOURCE_NUM_ID` and `INTEGRATION_ID` — both
  `CAST(NULL...)` with `ignoreColumn: true`.
- Renamed passthrough: `CREATED_ON_DT` <- source `CREATION_DATE`.
- Prior committed test case (git history commit `bf9c51e`) tested dead
  mapping-level logic, not the actual session-level overrides — this file is
  a correction of that, not just a recreate.
