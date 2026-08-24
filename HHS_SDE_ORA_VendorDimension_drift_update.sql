-- Deliberate data-drift update for the client failure demo.
--
-- Purpose: the workflow's transformation logic stays 100% correct -- this
-- only simulates the source (PO_VENDOR_SITES_ALL) receiving a real-world
-- update (vendor 9001's primary site phone number changed in EBS) AFTER
-- the last successful load into the staging target (W_VENDOR_DS). The
-- target therefore holds a now-stale PHONE value for VENDOR_ID 9001.
--
-- Re-running the DataCompare test case after this update should FAIL with
-- exactly one column-wise mismatch (PHONE, VENDOR_ID=9001), which is the
-- explainable "environment/data refresh gap, not a mapping defect" story.
--
-- Run against the same connection as the seed script: 192.168.6.103:1521:orcl, schema SH.

UPDATE PO_VENDOR_SITES_ALL
SET PHONE = '512-555-0175'
WHERE VENDOR_SITE_ID = 8001;

COMMIT;
