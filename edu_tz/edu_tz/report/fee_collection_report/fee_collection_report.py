import frappe
from frappe import _
from frappe.query_builder import Criterion
from frappe.query_builder.functions import MonthName, Sum, Year


def execute(filters=None):
	columns = get_columns(filters)
	data = []

	if filters.summary_based_on_month:
		month_summary, chart = get_summary_based_on_month(filters)

		if month_summary:
			data = month_summary

	if not filters.summary_based_on_month:
		chart = {}
		fee_data = get_fees(filters)

		if fee_data:
			data = fee_data

	return columns, data, chart


def get_filter_condtions(filters, fe, p_en, sg=None):
	conditions = []
	if filters.get("company"):
		conditions.append(fe.company == filters.company)
	if filters.get("academic_year"):
		conditions.append(fe.academic_year == filters.academic_year)
		conditions.append(p_en.academic_year == filters.academic_year)
		if sg:
			conditions.append(sg.academic_year == filters.academic_year)
	if sg and filters.get("program"):
		conditions.append(fe.program == filters.program)
		conditions.append(p_en.program == filters.program)
		conditions.append(sg.program == filters.program)

	return Criterion.all(conditions)


def get_columns(filters):
	if filters.summary_based_on_month:
		columns = [
			{"fieldname": "year", "fieldtype": "Data", "label": _("Year of Due Date")},
			{"fieldname": "month", "fieldtype": "Data", "label": _("Month")},
			{"fieldname": "program", "fieldtype": "Data", "label": _("Program")},
			{
				"fieldname": "total_amount_to_be_paid",
				"fieldtype": "Currency",
				"label": _("Total Fee to be Collected"),
			},
			{"fieldname": "total_paid_amount", "fieldtype": "Currency", "label": _("Total Fee Collected")},
			{"fieldname": "outstanding_amount", "fieldtype": "Currency", "label": _("Outstanding Amount")},
		]

	else:
		columns = [
			{"fieldname": "academic_year", "fieldtype": "Data", "label": _("Academic Year")},
			{"fieldname": "student_name", "fieldtype": "Data", "label": _("Student Name")},
			{"fieldname": "program", "fieldtype": "Data", "label": _("Program")},
			{"fieldname": "class_name", "fieldtype": "Data", "label": _("Class Name")},
			{"fieldname": "student_category", "fieldtype": "Data", "label": _("Fee Category")},
			{
				"fieldname": "total_amount_to_be_paid",
				"fieldtype": "Currency",
				"label": _("Fee to be Collected"),
			},
			{
				"fieldname": "1st_installment_paid_amount",
				"fieldtype": "Currency",
				"label": _("1st Installment Paid"),
			},
			{
				"fieldname": "2nd_installment_paid_amount",
				"fieldtype": "Currency",
				"label": _("2nd Installment Paid"),
			},
			{
				"fieldname": "3rd_installment_paid_amount",
				"fieldtype": "Currency",
				"label": _("3rd Installment Paid"),
			},
			{
				"fieldname": "4th_installment_paid_amount",
				"fieldtype": "Currency",
				"label": _("4th Installment Paid"),
			},
			{
				"fieldname": "5th_installment_paid_amount",
				"fieldtype": "Currency",
				"label": _("5th Installment Paid"),
			},
			{"fieldname": "total_paid_amount", "fieldtype": "Currency", "label": _("Total Fee Collected")},
			{"fieldname": "outstanding_amount", "fieldtype": "Currency", "label": _("Outstanding Amount")},
		]
	return columns


def get_fees(filters):
	fees_record = []
	student_records = []
	if not filters.summary_based_on_program:
		student_details, student_name_list = get_fee_details(filters)

		first_installment_list = []
		second_installment_list = []
		third_installment_list = []
		fourth_installment_list = []
		fifth_installment_list = []

		for st_name in student_name_list:
			total_amount_to_be_paid = total_unpaid_amount = 0

			for student_row in student_details:
				if (
					st_name["student"] == student_row["student"]
					and st_name["program"] == student_row["program"]
					and st_name["class_name"] == student_row["class_name"]
				):
					total_amount_to_be_paid += student_row["grand_total"]
					total_unpaid_amount += student_row["outstanding_amount"]

					if st_name not in first_installment_list:
						st_name.update(
							{"paid_amount1": student_row["grand_total"] - student_row["outstanding_amount"]}
						)
						first_installment_list.append(st_name)

					elif st_name not in second_installment_list:
						st_name["paid_amount2"] = (
							student_row["grand_total"] - student_row["outstanding_amount"]
						)
						second_installment_list.append(st_name)

					elif st_name not in third_installment_list:
						st_name.update(
							{"paid_amount3": student_row["grand_total"] - student_row["outstanding_amount"]}
						)
						third_installment_list.append(st_name)

					elif st_name not in fourth_installment_list:
						st_name.update(
							{"paid_amount4": student_row["grand_total"] - student_row["outstanding_amount"]}
						)
						fourth_installment_list.append(st_name)

					else:
						st_name.update(
							{"paid_amount5": student_row["grand_total"] - student_row["outstanding_amount"]}
						)
						fifth_installment_list.append(st_name)

			st_name.update(
				{
					"total_amount_to_be_paid": total_amount_to_be_paid,
					"outstanding_amount": total_unpaid_amount,
				}
			)
			student_records.append(st_name)

		for record in student_records:
			paid_amount = 0
			for first in first_installment_list:
				if (
					record["student"] == first["student"]
					and record["program"] == first["program"]
					and record["class_name"] == first["class_name"]
				):
					record.update(
						{
							"1st_installment_paid_amount": first["paid_amount1"],
						}
					)
					paid_amount += first["paid_amount1"]

			for second in second_installment_list:
				if (
					record["student"] == second["student"]
					and record["program"] == second["program"]
					and record["class_name"] == second["class_name"]
				):
					record.update({"2nd_installment_paid_amount": second["paid_amount2"]})
					paid_amount += second["paid_amount2"]

			for third in third_installment_list:
				if (
					record["student"] == third["student"]
					and record["program"] == third["program"]
					and record["class_name"] == third["class_name"]
				):
					record.update({"3rd_installment_paid_amount": third["paid_amount3"]})
					paid_amount += third["paid_amount3"]

			for fourth in fourth_installment_list:
				if (
					record["student"] == fourth["student"]
					and record["program"] == fourth["program"]
					and record["class_name"] == fourth["class_name"]
				):
					record.update({"4th_installment_paid_amount": fourth["paid_amount4"]})
					paid_amount += fourth["paid_amount4"]

			for fifth in fifth_installment_list:
				if (
					record["student"] == fifth["student"]
					and record["program"] == fifth["program"]
					and record["class_name"] == fifth["class_name"]
				):
					record.update({"5th_installment_paid_amount": fifth["paid_amount5"]})
					paid_amount += fifth["paid_amount5"]

			record["total_paid_amount"] = paid_amount
			fees_record.append(record)
	return fees_record


def get_fee_details(filters):
	name_list = []
	student_list = []
	student_details = []

	fe = frappe.qb.DocType("Fees")
	p_en = frappe.qb.DocType("Program Enrollment")
	sgs = frappe.qb.DocType("Student Group Student")
	sg = frappe.qb.DocType("Student Group")

	fee_details = (
		frappe.qb.from_(fe)
		.inner_join(p_en)
		.on(fe.student == p_en.student)
		.left_join(sgs)
		.on((sgs.student == fe.student) & (sgs.active == 1))
		.left_join(sg)
		.on((sgs.parent == sg.name) & (sg.disabled == 0))
		.select(
			fe.due_date,
			fe.student,
			fe.student_name,
			fe.program,
			fe.grand_total,
			fe.outstanding_amount,
			p_en.student_category,
			sg.academic_year,
			sgs.parent,
		)
		.where((fe.docstatus == 1) & (p_en.docstatus == 1) & get_filter_condtions(filters, fe, p_en, sg))
		.orderby(fe.due_date)
		.orderby(fe.student)
		.run(as_dict=True)
	)

	for student in fee_details:
		txt = student.parent
		program_class = ""
		if student.academic_year != 2020 and "FORM" in txt and "TODDLERS" not in txt:
			year, stream = txt.split("-")
			program_class += stream
		elif student.academic_year != 2020 and "FORM" not in txt and "TODDLERS" in txt:
			year, stream = txt.split("-")
			program_class += stream
		elif student.academic_year != 2020 and "FORM" not in txt and "TODDLERS" not in txt:
			year, pro, stream = txt.split("-")
			program_class += pro + " - " + stream
		else:
			program_class += txt

		student.update({"class_name": program_class})

		student_details.append(student)

		if student.student not in name_list:
			name_list.append(student.student)
			student_list.append(student)

	return student_details, student_list


def get_summary_based_on_month(filters):
	if filters.summary_based_on_month:
		chart = {}
		summary_data = []

		fe = frappe.qb.DocType("Fees")
		p_en = frappe.qb.DocType("Program Enrollment")

		fee_details = (
			frappe.qb.from_(fe)
			.inner_join(p_en)
			.on((fe.student == p_en.student) & (fe.program == p_en.program))
			.select(
				Year(fe.due_date).as_("year"),
				MonthName(fe.due_date).as_("month"),
				fe.program,
				Sum(fe.grand_total).as_("grand_total"),
				Sum(fe.outstanding_amount).as_("outstanding_amount"),
			)
			.where((fe.docstatus == 1) & (p_en.docstatus == 1) & get_filter_condtions(filters, fe, p_en))
			.groupby(MonthName(fe.due_date), fe.program)
			.orderby(Year(fe.due_date))
			.orderby(MonthName(fe.due_date))
			.orderby(fe.program)
			.run(as_dict=True)
		)

		for fee in fee_details:
			summary_data.append(
				{
					"year": fee.year,
					"month": fee.month,
					"program": fee.program,
					"total_paid_amount": fee.grand_total - fee.outstanding_amount,
					"outstanding_amount": fee.outstanding_amount,
					"total_amount_to_be_paid": fee.grand_total,
				}
			)

		chart = get_chart_data(summary_data)

		return summary_data, chart


def get_chart_data(summary_data):
	if not summary_data:
		return

	labels = []
	fees_collected = []
	outstanding_amount = []
	fees_to_be_collected = []

	for entry in summary_data:
		labels.append(entry.get("program"))
		fees_collected.append(entry.get("total_paid_amount"))
		outstanding_amount.append(entry.get("outstanding_amount"))
		fees_to_be_collected.append(entry.get("total_amount_to_be_paid"))

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Fee to be Collected"), "values": fees_to_be_collected},
				{"name": _("Fees Collected"), "values": fees_collected},
				{"name": _("Outstanding Amount"), "values": outstanding_amount},
			],
		},
		"type": "bar",
	}
