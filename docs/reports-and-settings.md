# Reports and settings

Module: **Edu Tz**. Sidebar: **Edu Tz → Reports** and **Edu Tz → Settings**.

## Reports

| Report | Type | Based on | What it shows |
|---|---|---|---|
| Fee Collection Report | Script | Fees | Per student: fee to be collected, collected, outstanding, and up to five installments, with class names derived from the student group. With **Summary Based on Month**, a month × program summary and a bar chart instead |
| Schools KPI | Script | Program Enrollment | Per program: rooms available and in use, utilisation rate, seating capacity, enrolled students and vacancies |

### Fee Collection Report

Filters: From Date, To Date, Company, Academic Year, Program, Summary Based on Month.

- **From Date and To Date currently have no effect.** The report code never reads them.
- Only submitted Fees and submitted Program Enrollments count.
- The **Program** filter applies to the per-student view only. The monthly summary ignores it.
- The class name comes from the student's active, enabled **Student Group** name, for example `2024-FORM ONE A` → `FORM ONE A`. Students without a group can make the report fail when no Academic Year filter is set.

### Schools KPI

Filters: Company, Academic Year. Rooms are counted per program through the Room's **edu_tz_program** field, so rooms with no program assigned don't appear. "Rooms in use" counts rooms that have a seating capacity set.

## Edu Tz Settings

A single doctype, System Manager only.

| Setting | Effect |
|---|---|
| Default Education Institution | Stored only. No edu_tz code reads it |
| Partial Payment | Sent to NMB as `allow_partial`. Also lets a partial registration-fee payment auto-approve an applicant |
| Enable Auto Program Enrollment | Turns on applicant auto-approval when the registration fee is paid |

## Navigation (Frappe v16)

edu_tz ships:
- a **Sidebar** for the Edu Tz module: Student Applicant Fees, NMB Callback, Reports, Settings
- an app **Dock**
- a **Desktop Icon**
- an app logo (a white graduation cap on blue)

The apps-screen tile opens the first Dock entry. These records reach a site on `bench --site <site> migrate`.
