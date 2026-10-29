// Copyright (c) 2020, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("NMB Callback", {
  refresh: function (frm) {
    frm.add_custom_button(__("Make Payment Entry"), function () {
      frappe.call({
        method: "edu_tz.edu_tz.nmb.api.make_payment_entry_from_call",
        args: {
          docname: frm.doc.name,
        },
      });
    });
  },
});
