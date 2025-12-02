from action.base import Action

class AddFeedingAction(Action):
    def execute(self, db_utils, **kwargs):
        a_id = kwargs.get('a_id')
        f_id = kwargs.get('f_id')
        amount = kwargs.get('amount')
        user_id = kwargs.get('user_id')
        
        success, msg = db_utils.add_feeding_record(a_id, f_id, amount, user_id)
        return {"success": success, "message": msg}
