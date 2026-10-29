"""NMB Bank fee integration: invoice submission, payment callbacks and reconciliation."""

import binascii
import json
import os
from datetime import datetime
from time import sleep
from typing import Any
from urllib.parse import quote, urlparse, urlunparse

import frappe
import requests
from csf_tz.csf_tz.doctype.csf_api_response_log.csf_api_response_log import add_log
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from frappe import _
from frappe.query_builder.functions import Coalesce, IfNull, Max, Sum
from frappe.utils import cint, flt, get_host_name
from frappe.utils.background_jobs import enqueue
from frappe.utils.password import get_decrypted_password

CALLBACK_METHOD = "edu_tz.edu_tz.nmb.api.receive_callback"


class ToObject:
	def __init__(self, data):
		self.__dict__ = json.loads(data)


def get_callback_url(callback_token: str) -> str:
	return f"https://{get_host_name()}/api/method/{CALLBACK_METHOD}?token={callback_token}"


def set_callback_token(doc, method):
	send_fee_details_to_bank = frappe.get_value("Company", doc.company, "send_fee_details_to_bank") or 0
	if not send_fee_details_to_bank:
		return
	doc.callback_token = binascii.hexlify(os.urandom(14)).decode()
	series = frappe.get_value("Company", doc.company, "nmb_series") or ""
	if not series:
		frappe.throw(_("Please set NMB User Series in Company {0}").format(doc.company))
	reference = str(series) + "F" + str(doc.name)
	if not doc.abbr:
		doc.abbr = frappe.get_value("Company", doc.company, "abbr") or ""
	doc.bank_reference = reference.replace("-", "").replace("FEE" + doc.abbr, "")
	if method == "invoice_submission":
		doc.save()
		# nosemgrep: frappe-manual-commit -- the token is sent to the bank next and must be persisted first
		frappe.db.commit()


def get_nmb_token(company):
	url = frappe.get_value("Company", company, "nmb_url")
	if not url:
		frappe.throw(_("Please set NMB URL in Company {0}").format(company))
	url = url + "auth"
	username = frappe.get_value("Company", company, "nmb_username")
	if not username:
		frappe.throw(_("Please set NMB User Name in Company {0}").format(company))
	password = get_decrypted_password("Company", company, "nmb_password")
	if not password:
		frappe.throw(_("Please set NMB Password in Company {0}").format(company))
	data = {
		"username": username,
		"password": password,
	}
	for i in range(3):
		try:
			r = requests.post(url, data=json.dumps(data), timeout=5)
			r.raise_for_status()
			frappe.logger().debug({"get_nmb_token webhook_success": r.text})
			if json.loads(r.text):
				add_log(
					request_type="NMB token",
					request_url=url,
					request_header="no header",
					request_body=json.dumps(data),
					response_data=json.loads(r.text),
				)
			if json.loads(r.text)["status"] == 1:
				return json.loads(r.text)["token"]
			else:
				frappe.throw(json.loads(r.text))
		except Exception as e:
			frappe.logger().debug({"get_nmb_token webhook_error": e, "try": i + 1})
			sleep(3 * i + 1)
			if i != 2:
				continue
			else:
				raise e


def send_nmb(method, data, company):
	url = frappe.get_value("Company", company, "nmb_url")
	if not url:
		frappe.throw(_("Please set NMB URL in Company {0}").format(company))
	data["token"] = get_nmb_token(company)
	url = url + str(method)
	for i in range(3):
		try:
			r = requests.post(url, data=json.dumps(data), timeout=5)
			r.raise_for_status()
			frappe.logger().debug({"send_nmb webhook_success": r.text})
			if json.loads(r.text):
				add_log(
					request_type="NMB " + method,
					request_url=url,
					request_header="no header",
					request_body=json.dumps(data),
					response_data=json.loads(r.text),
				)
			if json.loads(r.text)["status"] == 1:
				frappe.msgprint(_("Response from bank:") + "<br><hr>" + json.loads(r.text)["description"])
				return json.loads(r.text)
			else:
				if json.loads(r.text)["description"] == "Duplicate Invoice Number":
					return json.loads(r.text)
				frappe.msgprint(_("Error detected at bank:") + "<br><hr>" + json.loads(r.text)["description"])
				frappe.throw(json.loads(r.text))
		except Exception as e:
			frappe.logger().debug({"send_nmb webhook_error": e, "try": i + 1})
			sleep(3 * i + 1)
			if i != 2:
				continue
			else:
				raise e


@frappe.whitelist()
def invoice_submission(doc: Any = None, method: Any = None, fees_name: Any = None):
	if not doc and fees_name:
		doc = frappe.get_doc("Fees", fees_name)
	send_fee_details_to_bank = frappe.get_value("Company", doc.company, "send_fee_details_to_bank") or 0
	if not send_fee_details_to_bank:
		return

	partial_payment = frappe.db.get_single_value("Edu Tz Settings", "partial_payment")
	partial_payment = "TRUE" if partial_payment else "FALSE"

	if not doc.callback_token:
		frappe.msgprint(
			_("This fee is not set with a token to be sent to the Bank. Generating the token..."),
			alert=True,
		)
		set_callback_token(doc, "invoice_submission")
	series = frappe.get_value("Company", doc.company, "nmb_series") or ""
	if not series:
		frappe.throw(_("Please set NMB User Series in Company {0}").format(doc.company))
	data = {
		"reference": doc.bank_reference,
		"student_name": doc.student_name,
		"student_id": doc.student,
		"amount": doc.grand_total,
		"type": "Fees Invoice",
		"code": 10,
		"allow_partial": partial_payment,
		"callback_url": get_callback_url(doc.callback_token),
	}
	send_nmb("invoice_submission", data, doc.company)


# nosemgrep: guest-whitelisted-method -- NMB posts payment callbacks unauthenticated
@frappe.whitelist(allow_guest=True)
def receive_callback(*args, **kwargs):
	r = frappe.request
	url = url_fix(r.url.replace("+", " "))
	message = parse_request_body(r.get_data())
	parsed_url = urlparse(url)
	message["fees_token"] = parsed_url[4][6:]
	message["doctype"] = "NMB Callback"
	nmb_doc = frappe.get_doc(message)

	if nmb_doc.insert(ignore_permissions=True):
		frappe.response["status"] = 1
		frappe.response["description"] = "success"
	else:
		frappe.response["description"] = "insert failed"
		frappe.response["http_status_code"] = 409

	enqueue(
		method=make_payment_entry,
		queue="short",
		timeout=10000,
		is_async=True,
		kwargs=nmb_doc,
	)


def parse_request_body(body: bytes) -> dict:
	if not body:
		frappe.throw(_("This has no body!"))
	msgs = ToObject(body.decode("utf-8"))
	return {key: value for key, value in msgs.__dict__.items() if value}


def make_payment_entry(method="callback", **kwargs):
	for nmb_doc in kwargs.values():
		doc_info = get_fee_info(nmb_doc.reference)
		nmb_amount = flt(nmb_doc.amount)
		frappe.flags.ignore_account_permission = True
		if doc_info["doctype"] == "Fees":
			if method == "callback":
				# nosemgrep: frappe-setuser -- guest callback must post GL entries as Administrator
				frappe.set_user("Administrator")
			make_fees_payment_entry(doc_info["name"], nmb_doc, nmb_amount)
			return nmb_doc

		elif doc_info["doctype"] == "Student Applicant Fees":
			doc = frappe.get_doc("Student Applicant Fees", doc_info["name"])
			if not doc.callback_token == nmb_doc.fees_token:
				return
			auto_approve_student_applicant(doc, nmb_doc)
			return nmb_doc


def auto_approve_student_applicant(fee_doc, nmb_doc):
	"""Approve the Student Applicant for Program Enrollment once its registration fee is paid.

	Controlled by Edu Tz Settings: "Enable Auto Program Enrollment" switches this on, and
	"Partial Payment" (the same setting sent to the bank) decides whether any payment is enough
	or the full registration fee is required. Applicants can always be approved or rejected manually.
	"""
	if not cint(frappe.db.get_single_value("Edu Tz Settings", "enable_auto_program_enrollment")):
		return
	allow_partial = cint(frappe.db.get_single_value("Edu Tz Settings", "partial_payment"))

	applicant = frappe.get_doc("Student Applicant", fee_doc.student)
	nmb_amount = flt(nmb_doc.amount)

	# only applicants waiting for the fee; never override a manual approval, rejection or admission
	if applicant.application_status != "Awaiting Registration Fees":
		applicant.add_comment(
			"Comment",
			_(
				"Registration fee payment of {0} received (bank receipt {1}) while status is {2}. "
				"Not auto-approved, please review."
			).format(nmb_amount, nmb_doc.receipt, applicant.application_status),
		)
		return

	# the callback being processed may not be committed yet, so add it separately; count each receipt once
	callback = frappe.qb.DocType("NMB Callback")
	receipts = (
		frappe.qb.from_(callback)
		.select(Max(callback.amount).as_("amount"))
		.where(
			(callback.reference == nmb_doc.reference)
			& (IfNull(callback.receipt, "") != (nmb_doc.receipt or ""))
		)
		.groupby(callback.receipt)
	).as_("receipts")
	previous = frappe.qb.from_(receipts).select(Coalesce(Sum(receipts.amount), 0)).run()[0][0]
	total_paid = flt(previous) + nmb_amount
	fully_paid = total_paid >= flt(fee_doc.grand_total)

	if not fully_paid and not allow_partial:
		applicant.add_comment(
			"Comment",
			_(
				"Partial registration fee payment received: {0} of {1} (bank receipt {2}). "
				"Waiting for full payment before auto-approval."
			).format(total_paid, fee_doc.grand_total, nmb_doc.receipt),
		)
		return

	frappe.db.set_value(
		"Student Applicant",
		applicant.name,
		{"application_status": "Approved", "paid": 1 if fully_paid else 0},
	)
	applicant.add_comment(
		"Comment",
		_(
			"Auto-approved for Program Enrollment after registration fee payment of {0} of {1} "
			"(bank receipt {2})."
		).format(total_paid, fee_doc.grand_total, nmb_doc.receipt),
	)


def make_fees_payment_entry(fees_name, nmb_doc, nmb_amount):
	bank_reference, receivable_account = frappe.get_value(
		"Fees", fees_name, ["bank_reference", "receivable_account"]
	)
	if bank_reference != nmb_doc.reference:
		return
	payment_entry = get_payment_entry(
		"Fees",
		fees_name,
		party_amount=nmb_amount,
		bank_amount=nmb_amount,
		party_type="Student",
		payment_type="Receive",
	)
	payment_entry.update(
		{
			"payment_date": nmb_doc.timestamp,
			"posting_date": nmb_doc.timestamp,
			"reference_no": nmb_doc.reference,
			"reference_date": nmb_doc.timestamp,
			"remarks": f"Payment Entry against Fees {fees_name} via NMB Bank Payment {nmb_doc.reference}",
			"paid_from": receivable_account,
			"party_account": receivable_account,
		}
	)
	payment_entry.flags.ignore_permissions = True
	payment_entry.save()
	payment_entry.submit()


# nosemgrep: guest-whitelisted-method -- NMB validates references unauthenticated
@frappe.whitelist(allow_guest=True)
def receive_validate_reference(*args, **kwargs):
	message = parse_request_body(frappe.request.get_data())
	doc_info = get_fee_info(message["reference"])
	if not doc_info["name"]:
		frappe.response["status"] = 0
		frappe.response["description"] = "Not Exist"
		return

	doc = frappe.get_doc(doc_info["doctype"], doc_info["name"])
	return dict(
		status=1,
		reference=doc.bank_reference,
		student_name=doc.student_name,
		student_id=doc.student,
		amount=doc.grand_total,
		type="Fees Invoice",
		code=10,
		allow_partial="FALSE",
		callback_url=get_callback_url(doc.callback_token),
		token=message["token"],
	)


def cancel_invoice(doc, method):
	send_fee_details_to_bank = frappe.get_value("Company", doc.company, "send_fee_details_to_bank") or 0
	if not send_fee_details_to_bank:
		return
	data = {
		"reference": str(doc.bank_reference),
	}
	message = send_nmb("invoice_cancel", data, doc.company)
	frappe.msgprint(str(message))


def reconciliation(doc=None, method=None):
	for company in frappe.get_all("Company", pluck="name"):
		if not frappe.get_value("Company", company, "nmb_username"):
			continue
		data = {"reconcile_date": datetime.today().strftime("%d-%m-%Y")}
		message = send_nmb("reconcilliation", data, company)
		if message["status"] != 1:
			continue
		for transaction in message["transactions"]:
			if not is_known_callback(transaction):
				continue
			doc_info = get_fee_info(message["reference"])
			if not doc_info["name"]:
				continue
			message["fees_token"] = frappe.get_value(doc_info["doctype"], doc_info["name"], "callback_token")
			message["doctype"] = "NMB Callback"
			enqueue(
				method=make_payment_entry,
				queue="short",
				timeout=10000,
				is_async=True,
				kwargs=frappe.get_doc(message),
			)


def is_known_callback(transaction) -> bool:
	callbacks = frappe.get_all(
		"NMB Callback",
		filters={"reference": transaction.reference, "receipt": transaction.receipt},
		pluck="name",
	)
	return len(callbacks) == 1


def get_fee_info(bank_reference):
	data = {"name": "", "doctype": "", "company": ""}
	for doctype in ("Fees", "Student Applicant Fees"):
		doc_list = frappe.get_all(
			doctype,
			filters={"bank_reference": bank_reference, "docstatus": 1},
			fields=["name", "company"],
		)
		if doc_list:
			data["name"] = doc_list[0]["name"]
			data["doctype"] = doctype
			data["company"] = doc_list[0]["company"]
			return data
	return data


@frappe.whitelist()
def make_payment_entry_from_call(docname: Any):
	nmb_doc = frappe.get_doc("NMB Callback", docname)
	make_payment_entry(method="frontend", kwargs=nmb_doc)


def url_fix(url: str) -> str:
	"""Percent-encodes the non-ASCII characters of a URL."""
	s = url.replace("\\", "/")

	if s.startswith("file://") and s[7:8].isalpha() and s[8:10] in (":/", "|/"):
		s = f"file:///{s[7:]}"

	url = urlparse(s)
	path = quote(url.path, safe="/%+$!*'(),")
	qs = quote(url.query, safe=":&%=+$!*'(),")
	anchor = quote(url.fragment, safe=":&%=+$!*'(),")
	# urlunparse order is (scheme, netloc, path, params, query, fragment); the query must stay
	# in the query slot or "?token=..." turns into ";token=..." and the callback token is lost
	return urlunparse((url.scheme, url.netloc, path, url.params, qs, anchor))
