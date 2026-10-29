# Copyright (c) 2020, Aakvatech and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

# The tests use the site's Company and ignore mandatory links, so skip ERPNext/education test records.
test_ignore = [
	"Academic Term",
	"Academic Year",
	"Account",
	"Company",
	"Cost Center",
	"Fee Schedule",
	"Fee Structure",
	"Letter Head",
	"Print Heading",
	"Program",
	"Program Enrollment",
	"Student Applicant",
	"Student Batch Name",
	"Student Category",
]


class TestStudentApplicantFees(IntegrationTestCase):
	"""after_insert stamps the bank fields only when the company sends fee details to NMB."""

	def setUp(self):
		self.company = frappe.db.get_value("Company", {}, "name")

	def make_fees(self):
		return frappe.get_doc(
			{
				"doctype": "Student Applicant Fees",
				"company": self.company,
				"student_name": "Test Applicant",
				"posting_date": frappe.utils.today(),
				"due_date": frappe.utils.today(),
				"grand_total": 100,
			}
		)

	def test_bank_fields_set_when_enabled(self):
		frappe.db.set_value("Company", self.company, {"send_fee_details_to_bank": 1, "nmb_series": "TST"})

		doc = self.make_fees()
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		self.assertTrue(doc.callback_token)
		self.assertTrue(doc.bank_reference.startswith("TST"))

	def test_bank_fields_skipped_when_disabled(self):
		frappe.db.set_value("Company", self.company, "send_fee_details_to_bank", 0)

		doc = self.make_fees()
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		self.assertFalse(doc.callback_token)
		self.assertFalse(doc.bank_reference)

	def test_missing_series_throws(self):
		frappe.db.set_value("Company", self.company, {"send_fee_details_to_bank": 1, "nmb_series": ""})

		with self.assertRaises(frappe.ValidationError):
			self.make_fees().insert(ignore_permissions=True, ignore_mandatory=True)

	def test_submit_skips_bank_when_disabled(self):
		frappe.db.set_value("Company", self.company, "send_fee_details_to_bank", 0)
		doc = self.make_fees()
		doc.insert(ignore_permissions=True, ignore_mandatory=True)

		target = "edu_tz.edu_tz.doctype.student_applicant_fees.student_applicant_fees.invoice_submission"
		with patch(target) as invoice_submission:
			doc.submit()
		invoice_submission.assert_not_called()
