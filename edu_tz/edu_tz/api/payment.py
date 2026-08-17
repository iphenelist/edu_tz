from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate
from erpnext.accounts.utils import update_voucher_outstanding


def on_submit(doc, method):
    create_sales_invoice(doc)


def create_sales_invoice(doc):
    if (
        doc.party_type == "Student"
        and len(doc.references) > 0
        and doc.references[0].reference_doctype == "Fees"
    ):
        fees_doc = frappe.get_doc("Fees", doc.references[0].reference_name)
        if not fees_doc.components:
            frappe.throw(_("Fees document {0} has no fee components").format(fees_doc.name))
        item_name = fees_doc.components[0].fees_category
        income_account = fees_doc.sales_invoice_income_account
        customer = frappe.get_value("Student", doc.party, "customer")
        if not customer:
            frappe.throw(_("Please set Customer in Student record"))
        if not frappe.db.exists("Customer", customer):
            frappe.throw(
                _("Customer {0} linked to Student {1} does not exist").format(customer, doc.party)
            )
        cost_center = frappe.get_value("Company", doc.company, "cost_center")
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.customer = customer
        sales_invoice.remarks = "Payment Entry: " + doc.name
        sales_invoice.due_date = getdate()
        sales_invoice.company = doc.company
        sales_invoice.fees = fees_doc.name
        sales_invoice.payment_entry = doc.name
        sales_invoice.cost_center = cost_center
        sales_invoice.is_pos = 0

        sales_invoice.append(
            "items",
            {
                "item_code": item_name,
                "item_name": item_name,
                "description": item_name,
                "qty": 1,
                "uom": "Unit",
                "conversion_factor": 1,
                "rate": doc.paid_amount,
                "amount": doc.paid_amount,
                "cost_center": cost_center,
                "income_account": income_account,
            },
        )

        sales_invoice.flags.ignore_permissions = True
        frappe.flags.ignore_account_permission = True
        sales_invoice.set_missing_values()
        sales_invoice.save(ignore_permissions=True)

        update_voucher_outstanding(
            "Fees",
            fees_doc.name,
            fees_doc.receivable_account,
            "Student",
            fees_doc.student,
        )

        frappe.msgprint(
            _("Draft Sales Invoice created {0}").format(sales_invoice.name), alert=True
        )
        return sales_invoice.name