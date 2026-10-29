app_name = "edu_tz"
app_title = "Edu Tz"
app_publisher = "Aakvatech"
app_description = "edu_tz"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@aakvatech.com"
app_license = "MIT"
required_apps = ["erpnext", "education", "csf_tz"]

app_logo_url = "/assets/edu_tz/images/edu_tz-logo.svg"

# No "route": a bare `/desk/<module>` is not a page in v16, so the apps screen lands on the
# first entry of the app's Dock (the Edu Tz sidebar) instead.
add_to_apps_screen = [
	{
		"name": "edu_tz",
		"logo": app_logo_url,
		"title": "Edu Tz",
	}
]

# csf_tz owns the CSF API Response Log used for NMB request logging and the
# Company fields the Education section is inserted after.

doctype_js = {
	"Company": "public/js/company.js",
	"Fees": "public/js/fees.js",
	"Payment Reconciliation": "public/js/payment_reconciliation.js",
	"Program Enrollment": "public/js/program_enrollment.js",
	"Program Enrollment Tool": "public/js/program_enrollment_tool.js",
	"Student Applicant": "public/js/student_applicant.js",
}

doctype_list_js = {
	"Custom Field": "patches/custom_fields/custom_field.js",
	"Property Setter": "patches/property_setter/property_setter.js",
}

after_install = [
	"edu_tz.patches.custom_fields.create_custom_fields.execute",
	"edu_tz.patches.property_setter.create_property_setters.execute",
]

after_migrate = after_install

# create_course_enrollments is called from on_submit, so no doc_event can replace it.
# nosemgrep: override-doctype-class
override_doctype_class = {
	"Program Enrollment": "edu_tz.edu_tz.overrides.program_enrollment.EduTzProgramEnrollment",
}

doc_events = {
	"Student": {
		"after_insert": "edu_tz.edu_tz.api.student.after_insert",
		"validate": "edu_tz.edu_tz.api.student.validate",
	},
	"Payment Entry": {
		"on_submit": "edu_tz.edu_tz.api.payment.on_submit",
	},
	"Sales Invoice": {
		"on_submit": "edu_tz.edu_tz.api.sales_invoice.on_submit",
	},
	"Fees": {
		"before_insert": "edu_tz.edu_tz.overrides.fees.set_fee_abbr",
		"after_insert": "edu_tz.edu_tz.nmb.api.set_callback_token",
		"on_submit": "edu_tz.edu_tz.nmb.api.invoice_submission",
		"before_cancel": "edu_tz.edu_tz.overrides.fees.on_cancel_fees",
	},
	"Program Enrollment": {
		"before_submit": "edu_tz.edu_tz.overrides.program_enrollment.validate_submit_program_enrollment",
	},
	"Student Applicant": {
		"on_update_after_submit": "edu_tz.edu_tz.overrides.student_applicant.make_student_applicant_fees",
	},
}

scheduler_events = {
	"daily": [
		"edu_tz.edu_tz.nmb.api.reconciliation",
	],
}
