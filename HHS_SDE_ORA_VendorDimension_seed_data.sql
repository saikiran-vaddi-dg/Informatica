-- Seed data for the HHS_SDE_ORA_VendorDimension demo workflow.
--
-- Purpose: realistic rows for the two EBS-style source tables and the
-- staging target table, chosen so that Run 1 of the DataCompare test case
-- (JDBC 1 = actual W_VENDOR_DS, JDBC 2 = expected rebuild from PO_VENDORS /
-- PO_VENDOR_SITES_ALL) PASSES -- i.e. the target already holds exactly what
-- the mapping's documented rules would produce from this source data.
--
-- Run this against whichever JDBC connection(s) back the "PO_VENDORS" /
-- "PO_VENDOR_SITES_ALL" (source) and "W_VENDOR_DS" (target) data sources
-- once they're registered in the DataOps container -- table/schema
-- ownership wasn't resolvable this session because dataops_mcp is not
-- authenticated (list_data_sources could not be called). Adjust
-- schema-qualification as needed for the actual target database.

-- ============================================================
-- Source: PO_VENDORS
-- ============================================================
CREATE TABLE PO_VENDORS (
    VENDOR_ID               NUMBER(15)      NOT NULL PRIMARY KEY,
    VENDOR_NAME             VARCHAR2(240),
    SEGMENT1                VARCHAR2(30),
    VENDOR_TYPE_LOOKUP_CODE VARCHAR2(30),
    ENABLED_FLAG            VARCHAR2(1),
    DUNS_NUMBER             VARCHAR2(30),
    LAST_UPDATE_DATE        DATE,
    LAST_UPDATED_BY         NUMBER(15),
    CREATION_DATE           DATE,
    CREATED_BY              NUMBER(15)
);

INSERT INTO PO_VENDORS (VENDOR_ID, VENDOR_NAME, SEGMENT1, VENDOR_TYPE_LOOKUP_CODE, ENABLED_FLAG, DUNS_NUMBER, LAST_UPDATE_DATE, LAST_UPDATED_BY, CREATION_DATE, CREATED_BY) VALUES
(9001, 'Acme Medical Supplies',   'V-1001', 'SUPPLIER', 'Y', '123456789', DATE '2026-06-15', 4021, DATE '2024-02-10', 4021);
INSERT INTO PO_VENDORS (VENDOR_ID, VENDOR_NAME, SEGMENT1, VENDOR_TYPE_LOOKUP_CODE, ENABLED_FLAG, DUNS_NUMBER, LAST_UPDATE_DATE, LAST_UPDATED_BY, CREATION_DATE, CREATED_BY) VALUES
(9002, 'Lonestar Lab Services',   'V-1002', 'SUPPLIER', 'Y', '234567890', DATE '2026-05-02', 4021, DATE '2023-11-22', 4033);
INSERT INTO PO_VENDORS (VENDOR_ID, VENDOR_NAME, SEGMENT1, VENDOR_TYPE_LOOKUP_CODE, ENABLED_FLAG, DUNS_NUMBER, LAST_UPDATE_DATE, LAST_UPDATED_BY, CREATION_DATE, CREATED_BY) VALUES
(9003, 'Gulf Coast Logistics',    'V-1003', 'CARRIER',  'N', '345678901', DATE '2026-01-30', 4033, DATE '2022-08-04', 4021);
-- 9003 is disabled (ENABLED_FLAG='N') -- the workflow's Filter drops it, so it
-- must NOT appear in W_VENDOR_DS below. This exercises the filter rule.

-- ============================================================
-- Source: PO_VENDOR_SITES_ALL
-- ============================================================
CREATE TABLE PO_VENDOR_SITES_ALL (
    VENDOR_SITE_ID          NUMBER(15)      NOT NULL PRIMARY KEY,
    VENDOR_ID               NUMBER(15),
    ADDRESS_LINE1           VARCHAR2(240),
    CITY                    VARCHAR2(60),
    STATE                   VARCHAR2(150),
    ZIP                     VARCHAR2(60),
    COUNTRY                 VARCHAR2(25),
    PHONE                   VARCHAR2(20),
    PRIMARY_PAY_SITE_FLAG   VARCHAR2(1)
);

INSERT INTO PO_VENDOR_SITES_ALL (VENDOR_SITE_ID, VENDOR_ID, ADDRESS_LINE1, CITY, STATE, ZIP, COUNTRY, PHONE, PRIMARY_PAY_SITE_FLAG) VALUES
(8001, 9001, '100 Main St',        'Austin', 'TX', '73301', NULL,   '512-555-0100', 'Y');
-- COUNTRY is NULL for 9001 on purpose -- exercises the IIF(ISNULL(COUNTRY),'USA',COUNTRY) fallback.
INSERT INTO PO_VENDOR_SITES_ALL (VENDOR_SITE_ID, VENDOR_ID, ADDRESS_LINE1, CITY, STATE, ZIP, COUNTRY, PHONE, PRIMARY_PAY_SITE_FLAG) VALUES
(8002, 9001, '900 Old Warehouse Rd','Austin', 'TX', '73344', 'USA',  '512-555-0199', 'N');
-- 8002 is a second, non-primary site for the same vendor -- exercises the
-- Joiner's PRIMARY_PAY_SITE_FLAG='Y' filter (must NOT be the one selected).
INSERT INTO PO_VENDOR_SITES_ALL (VENDOR_SITE_ID, VENDOR_ID, ADDRESS_LINE1, CITY, STATE, ZIP, COUNTRY, PHONE, PRIMARY_PAY_SITE_FLAG) VALUES
(8003, 9002, '200 Congress Ave',   'Dallas', 'TX', '75201', 'USA',  '214-555-0200', 'Y');
INSERT INTO PO_VENDOR_SITES_ALL (VENDOR_SITE_ID, VENDOR_ID, ADDRESS_LINE1, CITY, STATE, ZIP, COUNTRY, PHONE, PRIMARY_PAY_SITE_FLAG) VALUES
(8004, 9003, '500 Port Rd',        'Houston','TX', '77002', 'USA',  '713-555-0300', 'Y');
-- 8004 belongs to disabled vendor 9003 -- irrelevant to the target, included
-- only for source-side realism.

-- ============================================================
-- Target (staging): W_VENDOR_DS
-- Rows below are exactly what the mapping's rules produce from the source
-- data above -- Run 1 should therefore PASS with zero mismatches.
-- ============================================================
CREATE TABLE W_VENDOR_DS (
    VENDOR_ID           VARCHAR2(30),
    VENDOR_NAME         VARCHAR2(240),
    VENDOR_NUMBER       VARCHAR2(30),
    VENDOR_TYPE_CODE    VARCHAR2(30),
    DUNS_NUMBER         VARCHAR2(30),
    ADDRESS_LINE1       VARCHAR2(240),
    CITY                VARCHAR2(60),
    STATE               VARCHAR2(150),
    ZIP                 VARCHAR2(60),
    COUNTRY             VARCHAR2(25),
    PHONE               VARCHAR2(20),
    INTEGRATION_ID      VARCHAR2(80)    NOT NULL,
    TENANT_ID           VARCHAR2(80),
    DATASOURCE_NUM_ID   NUMBER(10)      NOT NULL,
    SRC_EFF_FROM_DT     DATE            NOT NULL,
    ACTIVE_FLG          CHAR(1),
    CREATED_ON_DT       DATE,
    CHANGED_ON_DT       DATE,
    CREATED_BY_ID       VARCHAR2(80),
    CHANGED_BY_ID       VARCHAR2(80),
    PRIMARY KEY (INTEGRATION_ID, DATASOURCE_NUM_ID, SRC_EFF_FROM_DT)
);

INSERT INTO W_VENDOR_DS (VENDOR_ID, VENDOR_NAME, VENDOR_NUMBER, VENDOR_TYPE_CODE, DUNS_NUMBER, ADDRESS_LINE1, CITY, STATE, ZIP, COUNTRY, PHONE, INTEGRATION_ID, TENANT_ID, DATASOURCE_NUM_ID, SRC_EFF_FROM_DT, ACTIVE_FLG, CREATED_ON_DT, CHANGED_ON_DT, CREATED_BY_ID, CHANGED_BY_ID) VALUES
('9001', 'Acme Medical Supplies', 'V-1001', 'SUPPLIER', '123456789', '100 Main St',     'Austin', 'TX', '73301', 'USA', '512-555-0100', 'VND~9001', 'HHS_DEFAULT', 301, DATE '1900-01-01', 'Y', DATE '2024-02-10', DATE '2026-06-15', '4021', '4021');
-- COUNTRY resolved to 'USA' via the fallback rule (source COUNTRY was NULL).
INSERT INTO W_VENDOR_DS (VENDOR_ID, VENDOR_NAME, VENDOR_NUMBER, VENDOR_TYPE_CODE, DUNS_NUMBER, ADDRESS_LINE1, CITY, STATE, ZIP, COUNTRY, PHONE, INTEGRATION_ID, TENANT_ID, DATASOURCE_NUM_ID, SRC_EFF_FROM_DT, ACTIVE_FLG, CREATED_ON_DT, CHANGED_ON_DT, CREATED_BY_ID, CHANGED_BY_ID) VALUES
('9002', 'Lonestar Lab Services', 'V-1002', 'SUPPLIER', '234567890', '200 Congress Ave','Dallas', 'TX', '75201', 'USA', '214-555-0200', 'VND~9002', 'HHS_DEFAULT', 301, DATE '1900-01-01', 'Y', DATE '2023-11-22', DATE '2026-05-02', '4033', '4021');
-- Vendor 9003 is intentionally absent: ENABLED_FLAG='N' means the workflow's
-- Filter drops it before it ever reaches the target.
