# NMB Bank fee integration

Module: **Edu Tz**. Sidebar: **Edu Tz → NMB Callback**. Code: `edu_tz/edu_tz/nmb/api.py`.

Schools collect fees through NMB Bank. Each fee document gets a bank reference. The bank holds the invoice, and when a parent pays, NMB calls back into the site so the payment can be recorded automatically.

The integration moved here from `csf_tz`. Invoices sent before the move still carry `csf_tz.bank_api.receive_callback` as their callback URL, and csf_tz forwards those calls to this app.

## Switching it on (per Company)

Nothing is sent to the bank unless the Company has **Send Fee details to Bank** ticked. These Company fields sit in the **Education** section, which edu_tz adds as custom fields:

| Field | Purpose |
|---|---|
| `send_fee_details_to_bank` | Master switch for this company |
| `nmb_url` | Base URL of the NMB API, ending in `/`. `auth`, `invoice_submission`, `invoice_cancel` and `reconcilliation` are appended to it |
| `nmb_username`, `nmb_password` | API credentials. The password is stored encrypted |
| `nmb_series` | Prefix for bank references |
| `fee_bank_account` | Bank account used for fee receipts |
| `student_applicant_fees_revenue_account` | Income account for registration fees |

**Edu Tz Settings → Partial Payment** is sent to the bank as `allow_partial` (`TRUE`/`FALSE`) with every invoice.

## Flow for a Fees document

1. **Insert**: `set_fee_abbr` copies the company from the Fee Structure, and `set_callback_token` creates a random callback token and the bank reference: `nmb_series` + `F` + the document name, with dashes and `FEE<abbr>` removed.
2. **Submit**: `invoice_submission` gets an auth token from NMB, then posts the invoice: reference, student, amount, `allow_partial`, and a callback URL of `https://<host>/api/method/edu_tz.edu_tz.nmb.api.receive_callback?token=<callback token>`. Both bank calls retry 3 times, with a 5-second timeout each. Every request and response is logged in csf_tz's **CSF API Response Log**.
3. **Payment**: NMB posts to `receive_callback`, a guest endpoint. It saves an **NMB Callback** record (reference, receipt, amount, channel, timestamp, and the token from the URL) and queues `make_payment_entry`.
4. **Payment Entry**: for a Fees reference, a Payment Entry is created and submitted as Administrator, for the callback amount, against the Fees receivable account.
5. **Cancel**: cancelling the Fees unlinks its payment entries and sends `invoice_cancel` to NMB.

The **Invoice Submission** button on a submitted Fees form re-sends the invoice by hand.

## Flow for Student Applicant Fees

The same pattern, but the reference uses `R` instead of `F`. A payment callback doesn't create a Payment Entry. It goes to the auto-approval step described in [admissions-and-fees.md](admissions-and-fees.md).

## Bank-facing endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `edu_tz.edu_tz.nmb.api.receive_callback` | Guest | NMB reports a payment |
| `edu_tz.edu_tz.nmb.api.receive_validate_reference` | Guest | NMB checks that a reference exists before taking payment. Returns the student, amount and callback URL |

Both have to be open to guests because NMB doesn't log in. `receive_callback` checks the callback token only for Student Applicant Fees. For Fees, it matches on the bank reference alone.

## NMB Callback (DocType)

Naming `NMBC-.YY.-.######`. System Manager only. One row per callback received, so a repeated callback creates a second row. The **Make Payment Entry** button re-runs the payment step for a single callback, which is useful when the queued job failed.

## Daily reconciliation

The scheduler runs `reconciliation` daily. For each company with an NMB username, it asks NMB for that day's transactions and queues payment entries.

> **Known issue:** this job looks up `message["reference"]` (the whole response) instead of each transaction's reference. It also only processes transactions that already have exactly one NMB Callback. Treat reconciliation as unreliable until it's fixed and tested against the bank's sandbox.
