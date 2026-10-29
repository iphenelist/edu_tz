# Program enrollment

Module: **Edu Tz**, which extends education's **Program Enrollment** and **Program Enrollment Tool**. These forms appear in education's sidebar, not in the Edu Tz sidebar.

## Program Enrollment

- **Class override:** `EduTzProgramEnrollment` replaces education's controller. On submit, it enrolls the student in **every course of the program**, not only the courses listed on the enrollment.
- **Student Category is required to submit.** A `before_submit` hook stops the submit without it.
- **Fee schedule:** changing the Program or Student Category fills the **Fees** table from the program's **Program Fee** rows. edu_tz adds that table to Program. Only rows matching the student category, and whose Fee Structure belongs to the enrollment's academic year (and term, if one is set), are used. The table is refilled on save if it's empty.

## Program Enrollment Tool

The **Enroll All Students** button replaces the standard enroll action, which times out on large batches:

- 30 students or fewer are enrolled straight away.
- More than 30 are enrolled in a background job. A progress bar follows the job, and an alert says it was queued.

When the tool gets its students from **Student Applicant**, a reminder asks you to remove applicants who already have students created.

## Other education changes

| DocType | Change |
|---|---|
| Program | `company` field and a **Program Fee** table |
| Room | `edu_tz_program` (the program the room is assigned to, used by the Schools KPI report) |
| Student | `bank` select |
| Guardian, Fees, Fee Structure, Program, Program Enrollment, Program Fee, Student Applicant | property setters (17 in total), shipped in `patches/property_setter/property_setters_json/` |

Custom fields and property setters are re-applied on every `migrate`, from the JSON in `edu_tz/patches/`.
