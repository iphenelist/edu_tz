# Copyright (c) 2020, Aakvatech and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from edu_tz.edu_tz.nmb.api import get_callback_url, get_fee_info

# Payment Entry records come from ERPNext's test setup, not from this app.
test_ignore = ["Payment Entry"]


class TestNMBCallback(IntegrationTestCase):
	def test_callback_url_points_to_edu_tz(self):
		url = get_callback_url("abc123")
		self.assertTrue(url.endswith("/api/method/edu_tz.edu_tz.nmb.api.receive_callback?token=abc123"))

	def test_unknown_reference_resolves_to_nothing(self):
		self.assertEqual(get_fee_info("no-such-reference"), {"name": "", "doctype": "", "company": ""})

	def test_reference_resolves_to_student_applicant_fees(self):
		company = frappe.db.get_value("Company", {}, "name")
		doc = frappe.get_doc(
			{
				"doctype": "Student Applicant Fees",
				"company": company,
				"student_name": "Test Applicant",
				"posting_date": frappe.utils.today(),
				"due_date": frappe.utils.today(),
				"grand_total": 100,
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		doc.db_set({"bank_reference": "TSTREF001", "docstatus": 1})

		info = get_fee_info("TSTREF001")
		self.assertEqual(info, {"name": doc.name, "doctype": "Student Applicant Fees", "company": company})
