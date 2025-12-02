from action.base import Action

class GetReferenceDataAction(Action):
    def execute(self, db_utils, **kwargs):
        table_name = kwargs.get('table_name')
        data = db_utils.get_reference_data(table_name)
        return {"success": True, "data": data}
