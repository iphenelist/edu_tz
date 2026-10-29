import json
from typing import Any

import frappe
from education.education.api import enroll_student
from frappe import _

ENQUEUE_THRESHOLD = 30


@frappe.whitelist(methods=["POST"])
def enroll_all_students(self: Any):
	"""Enqueues the enrollment for large batches, since the standard tool times out on many students.

	:param self: Program Enrollment Tool as JSON
	"""
	self = frappe.get_doc(json.loads(self))

	if self.get_students_from == "Student Applicant":
		frappe.msgprint(_("Remove student applicants that are already created"))

	if len(self.students) > ENQUEUE_THRESHOLD:
		frappe.enqueue("edu_tz.edu_tz.overrides.program_enrollment_tool.enroll_students", self=self)
		return "queued"

	enroll_students(self=self)
	return len(self.students)


def enroll_students(self: Any):
	"""Copy of the education enrollment loop that accepts a deserialized doc so it can be enqueued."""
	total = len(self.students)
	for index, row in enumerate(self.students):
		frappe.publish_realtime(
			"program_enrollment_tool",
			dict(progress=[index + 1, total]),
			user=frappe.session.user,
		)
		if row.student:
			program_enrollment = frappe.new_doc("Program Enrollment")
			program_enrollment.student = row.student
			program_enrollment.student_name = row.student_name
			program_enrollment.program = self.new_program
			program_enrollment.academic_year = self.new_academic_year
			program_enrollment.academic_term = self.new_academic_term
			program_enrollment.student_batch_name = row.student_batch_name or self.new_student_batch
			program_enrollment.save()
		elif row.student_applicant:
			program_enrollment = enroll_student(row.student_applicant)
			program_enrollment.academic_year = self.academic_year
			program_enrollment.academic_term = self.academic_term
			program_enrollment.student_batch_name = row.student_batch_name or self.new_student_batch
			program_enrollment.save()
