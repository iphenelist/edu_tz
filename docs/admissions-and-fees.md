# Admissions, fees and accounting

Module: **Edu Tz**. Sidebar: **Edu Tz → Student Applicant Fees**. The rest of this flow happens on education's own forms (Student Applicant, Fees, Student), which edu_tz extends.

## Registration fee: Student Applicant → Student Applicant Fees

edu_tz adds `fee_structure`, `program_enrollment`, `student_applicant_fee` and `bank_reference` fields to **Student Applicant**.

1. Set a **Fee Structure** on the applicant and submit it.
2. If the Company sends fees to the bank, the form shows **Student Applicant Actions**:
   - **Reject**, while the status is *Applied*.
   - **Awaiting Registration Fees**, while the status is *Applied* or *Rejected*.
3. Moving the applicant to **Awaiting Registration Fees** creates and submits a **Student Applicant Fees** document from the Fee Structure. That covers the amount, accounts, cost center, program, year and term. The applicant stores the new fee's name and bank reference.
4. On submit, the fee is sent to NMB (see [nmb-bank-integration.md](nmb-bank-integration.md)).
5. Cancelling the Student Applicant Fees cancels it at the bank and resets the applicant to **Applied**.

### Student Applicant Fees (DocType)

Submittable, naming `RFEE-.abbr.-.YY.-`.

| Role | Rights |
|---|---|
| Academics User | read, write, create, delete (no submit) |
| Accounts User | read, write, create, submit, delete |
| Accounts Manager, System Manager | everything, including cancel |

Required fields: Student Applicant, Institution (Company), Date, Due Date and Receivable Account.

### Auto-approval on payment

When NMB reports a registration-fee payment, the applicant is approved automatically if all of these hold:

- **Edu Tz Settings → Enable Auto Program Enrollment** is on.
- The applicant is still **Awaiting Registration Fees**. Any other status gets a comment for manual review and is never overridden.
- Either the fee is fully paid, or **Partial Payment** is on. Each bank receipt is counted once, even if NMB repeats the callback.

Approval sets `application_status = Approved` and ticks `paid` only on full payment. It also leaves a comment with the amounts and the receipt number. A partial payment while Partial Payment is off only adds a comment.

## Students become Customers

When a **Student** is inserted, or saved without a customer, edu_tz creates a **Customer**. The customer group is always *Student*, and the territory, price list and language come from Selling and System Settings. The Customer's new `student` field links it back to the Student.

## Fees → Payment Entry → Sales Invoice → Journal Entry

edu_tz turns fee payments into revenue documents:

1. **Payment Entry submit** (party type Student, first reference a Fees): creates a **draft Sales Invoice** for the paid amount. Its item is the first fee component's category, and its income account is the Fees' **Sales Invoice Income Account**. The Fees outstanding amount is then updated.
2. **Sales Invoice submit** (only when its `fees` field is set): creates and submits a **Journal Entry**. It debits the Fees' Sales Invoice Income Account and credits the customer's receivable, referenced to the invoice.

The custom fields this needs:
- **Fees** and **Fee Structure**: `sales_invoice_income_account`
- **Sales Invoice**: `fees` and `payment_entry`
- **Fee Structure** and **Program Fee**: `default_fee_category`
