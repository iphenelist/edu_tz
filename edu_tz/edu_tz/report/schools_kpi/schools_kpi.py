# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe.utils import cstr


def execute(filters):
	columns = [
		{"fieldname": "class_name", "label": _("Class Name"), "fieldtype": "Data"},
		{
			"fieldname": "class_avilable",
			"label": _("No. of Classes Available"),
			"fieldtype": "Int",
		},
		{
			"fieldname": "class_in_use",
			"label": _("No. of Classes in Use"),
			"fieldtype": "Int",
		},
		{
			"fieldname": "rate",
			"label": _("Classroom Utilization Rate"),
			"fieldtype": "Data",
		},
		{
			"fieldname": "class_capacity",
			"label": _("Classes Capacity"),
			"fieldtype": "Int",
		},
		{
			"fieldname": "no_of_students",
			"label": _("No. of Students per Class"),
			"fieldtype": "Int",
		},
		{"fieldname": "vacancies", "label": _("No. of Vacancies"), "fieldtype": "Data"},
	]

	data = []
	enrollment_details = frappe.get_all(
		"Program Enrollment",
		filters={
			"docstatus": 1,
			"academic_year": filters.academic_year,
			"company": filters.company,
		},
		fields=["program", "count(student) as no_of_students"],
		group_by="program",
	)

	room = frappe.qb.DocType("Room")
	program = frappe.qb.DocType("Program")
	room_details = (
		frappe.qb.from_(room)
		.inner_join(program)
		.on(room.edu_tz_program == program.name)
		.select(
			program.name.as_("program"),
			Sum(room.seating_capacity).as_("total_students"),
			Count(room.room_name).as_("total_rooms"),
			Count(room.seating_capacity).as_("no_of_room_used"),
		)
		.where(program.company == filters.get("company"))
		.groupby(program.name)
		.run(as_dict=True)
	)

	for enroll in enrollment_details:
		for room in room_details:
			if enroll.program == room.program:
				d = enroll.no_of_students - room["total_students"]
				if d > 0:
					vacancies = "+" + cstr(d)
				else:
					vacancies = d

				data.append(
					{
						"class_name": enroll.program,
						"class_avilable": room["total_rooms"],
						"class_in_use": room["no_of_room_used"],
						"rate": cstr((room["no_of_room_used"] / room["total_rooms"]) * 100) + "%",
						"class_capacity": room["total_students"],
						"no_of_students": enroll.no_of_students,
						"vacancies": vacancies,
					}
				)

	return columns, data
