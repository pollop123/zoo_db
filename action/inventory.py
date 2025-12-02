from action.base import Action

class AddInventoryStockAction(Action):
    def execute(self, db_utils, **kwargs):
        f_id = kwargs.get('f_id')
        amount = kwargs.get('amount')
        user_id = kwargs.get('user_id')
        
        success, msg = db_utils.add_inventory_stock(f_id, amount, user_id)
        return {"success": success, "message": msg}

class GetInventoryReportAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_inventory_report()
        return {"success": True, "data": data}
