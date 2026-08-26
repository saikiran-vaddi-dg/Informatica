# HHS_SDE_ORA_ProgramActivity_Dimension

SDE mapping extracting Treasury program-activity/reporting-code data from
Oracle EBS Federal Financials (`FV_FACTS_PRC_HDR` outer-joined to
`FV_FACTS_PRC_DTL` and `FV_DACT_PRC_ALLOCATION`) into staging table
`WC_PROGRAM_ACTIVITY_DS`, with a conditional (CASE on `ALLOCATED_FLAG`)
source for the program-activity report code/description.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
