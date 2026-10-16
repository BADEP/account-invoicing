# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPickingInvoicingCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _run_picking_onchanges(self, record):
        record._onchange_invoice_state()

    def _run_line_onchanges(self, record):
        record._onchange_product_id()

    def picking_move_state(self, picking):
        self._run_picking_onchanges(picking)
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

    def create_invoice_wizard(self, pickings):
        wizard_obj = self.env["stock.invoice.onshipping"].with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard_values.update({"group": "partner_product"})
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "in", pickings.ids)]
        invoice = self.env["account.move"].search(domain)
        return invoice

    def return_picking_wizard(self, picking):
        # Return Picking: the stock.return.picking wizard was removed in
        # Odoo 20, returns are now draft pickings created by _create_return()
        picking_devolution = picking._create_return()
        self.assertTrue(picking_devolution, "Create returns fail.")
        picking_devolution.move_ids[0].product_uom_qty = 1
        picking_devolution.set_to_be_invoiced()
        return picking_devolution

    def create_backorder_wizard(self, picking):
        res_dict_for_back_order = picking.button_validate()
        backorder_wizard = Form(
            self.env[res_dict_for_back_order["res_model"]].with_context(
                **res_dict_for_back_order["context"]
            )
        ).save()
        backorder_wizard.process()
        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", picking.id)]
        )
        return backorder
