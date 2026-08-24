# HHS_SDE_ORA_VendorDimension

Synthetic demo SDE mapping extracting vendor master data from Oracle EBS
`PO_VENDORS`, joined to each vendor's primary pay-site address/phone from
`PO_VENDOR_SITES_ALL`, filtered to enabled vendors, and loaded into staging
table `W_VENDOR_DS`.

- [Extraction details](extraction.md)
- [HRD mapping / test cases & dataflows](hrd_mapping.md)
