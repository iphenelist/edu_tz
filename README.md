## Edu Tz

Tanzania-specific extensions to the Frappe **Education** app, by Aakvatech: NMB Bank fee collection, paid registration fees for student applicants, fee accounting in ERPNext, and school reports.

Branch `version-16-hotfix` targets Frappe, ERPNext and Education v16.

### Requirements

| App | Why |
|---|---|
| `erpnext` | Payment Entry, Sales Invoice, Journal Entry, Customer |
| `education` | Student, Student Applicant, Fees, Program Enrollment and the rest of the domain |
| `csf_tz` | **CSF API Response Log**, used to log every NMB request |

These are declared in `required_apps`, and `bench install-app edu_tz` installs them first.

### Install

```bash
bench get-app https://github.com/Aakvatech-Limited/edu_tz.git --branch version-16-hotfix
bench --site <site> install-app edu_tz
```

### Documentation

| Page | Covers |
|---|---|
| [NMB Bank fee integration](docs/nmb-bank-integration.md) | Company setup, invoice submission, callbacks, NMB Callback, reconciliation |
| [Admissions, fees and accounting](docs/admissions-and-fees.md) | Student Applicant Fees, auto-approval, Student → Customer, Payment Entry → Sales Invoice → Journal Entry |
| [Program enrollment](docs/enrollment.md) | Program Enrollment override, fee schedule, bulk enrollment tool, custom fields |
| [Reports and settings](docs/reports-and-settings.md) | Fee Collection Report, Schools KPI, Edu Tz Settings, v16 navigation |

### License

MIT
