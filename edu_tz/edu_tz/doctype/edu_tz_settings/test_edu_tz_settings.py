# Copyright (c) 2021, Aakvatech and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

# Company records come from ERPNext's test setup, not from this app.
test_ignore = ["Company"]


class TestEduTzSettings(IntegrationTestCase):
	def test_partial_payment_defaults_off(self):
		self.assertFalse(frappe.db.get_single_value("Edu Tz Settings", "partial_payment"))
