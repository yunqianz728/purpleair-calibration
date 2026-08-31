# Security policy

## Supported version

Version 2.x of the public application and the `main` branch receive security
and dependency fixes.

## Report a vulnerability

Please email `lianglu@berkeley.edu` with the subject
`PurpleAir calibration security report`. Include the affected component,
reproduction steps, potential impact, and any suggested mitigation.

Avoid opening a public issue until the maintainers have assessed the report.
Do not include API keys, personal data, or identifiable sensor-owner
information in reports or example files.

The application processes uploaded CSV files in the active session and limits
public runs to 100,000 rows. Users deploying their own copy remain responsible
for access control, dependency updates, and infrastructure monitoring.
