"""Guards the move of the education and NMB features from csf_tz into edu_tz."""

import frappe
from frappe.tests import IntegrationTestCase

from edu_tz.edu_tz.overrides.program_enrollment import get_fee_schedule
from edu_tz.patches.custom_fields import create_custom_fields
from edu_tz.patches.property_setter import create_property_setters

MOVED_DOCTYPES = ("Student Applicant Fees", "NMB Callback")

COMPANY_NMB_FIELDS = (
	"education_section",
	"send_fee_details_to_bank",
	"fee_bank_account",
	"student_applicant_fees_revenue_account",
	"nmb_series",
	"nmb_username",
	"nmb_password",
	"nmb_url",
)

EDUCATION_FIELDS = (
	"Fees-callback_token",
	"Fees-bank_reference",
	"Fees-abbr",
	"Fee Structure-sales_invoice_income_account",
	"Student Applicant-fee_structure",
	"Program-program_fee",
	"Room-edu_tz_program",
	"Customer-student",
)

PROPERTY_SETTERS = (
	"Fee Structure-title_field",
	"Program-program_fee-allow_bulk_edit",
	"Student Applicant-application_status-options",
)


class TestEducationMove(IntegrationTestCase):
	def test_moved_doctypes_belong_to_edu_tz(self):
		for doctype in MOVED_DOCTYPES:
			self.assertEqual(frappe.db.get_value("DocType", doctype, "module"), "Edu Tz")

	def test_json_custom_fields_exist(self):
		for name in EDUCATION_FIELDS + tuple(f"Company-{field}" for field in COMPANY_NMB_FIELDS):
			self.assertTrue(frappe.db.exists("Custom Field", name), name)

	def test_json_property_setters_exist(self):
		for name in PROPERTY_SETTERS:
			self.assertTrue(frappe.db.exists("Property Setter", name), name)

	def test_json_loaders_are_idempotent(self):
		custom_fields = frappe.db.count("Custom Field")
		property_setters = frappe.db.count("Property Setter")
		create_custom_fields.execute()
		create_property_setters.execute()
		self.assertEqual(frappe.db.count("Custom Field"), custom_fields)
		self.assertEqual(frappe.db.count("Property Setter"), property_setters)

	def test_json_loaders_skip_missing_doctypes(self):
		create_custom_fields.create_fields_from_json(
			[{"dt": "No Such DocType", "fieldname": "x", "fieldtype": "Data", "label": "X"}]
		)
		create_property_setters.create_property_setters_from_json(
			[
				{
					"name": "No Such DocType-main-track_changes",
					"doctype_or_field": "DocType",
					"doc_type": "No Such DocType",
					"property": "track_changes",
					"property_type": "Check",
					"value": "1",
				}
			]
		)
		self.assertFalse(frappe.db.exists("Custom Field", "No Such DocType-x"))
		self.assertFalse(frappe.db.exists("Property Setter", "No Such DocType-main-track_changes"))

	def test_program_enrollment_uses_edu_tz_controller(self):
		from edu_tz.edu_tz.overrides.program_enrollment import EduTzProgramEnrollment

		self.assertIsInstance(frappe.new_doc("Program Enrollment"), EduTzProgramEnrollment)

	def test_get_fee_schedule_without_matching_program(self):
		self.assertEqual(get_fee_schedule("No Such Program", "2099-2100"), [])

	def test_csf_tz_callback_shim_forwards_to_edu_tz(self):
		from csf_tz import bank_api

		from edu_tz.edu_tz.nmb import api

		self.assertIs(bank_api.get_callback_handler("receive_callback"), api.receive_callback)
