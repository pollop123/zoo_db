from action.base import Action

class AddAnimalStateAction(Action):
    def execute(self, db_utils, **kwargs):
        a_id = kwargs.get('a_id')
        weight = kwargs.get('weight')
        user_id = kwargs.get('user_id')
        
        success, msg = db_utils.add_animal_state(a_id, weight, user_id)
        return {"success": success, "message": msg}
