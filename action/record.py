from action.base import Action

class CorrectRecordAction(Action):
    def execute(self, db_utils, **kwargs):
        user_id = kwargs.get('user_id')
        table = kwargs.get('table')
        record_id = kwargs.get('record_id')
        col_name = kwargs.get('col_name')
        new_val = kwargs.get('new_val')
        
        success, msg = db_utils.correct_record(user_id, table, record_id, col_name, new_val)
        return {"success": success, "message": msg}

class GetRecentRecordsAction(Action):
    def execute(self, db_utils, **kwargs):
        table_name = kwargs.get('table_name')
        filter_id = kwargs.get('filter_id')
        
        data = db_utils.get_recent_records(table_name, filter_id)
        return {"success": True, "data": data}
