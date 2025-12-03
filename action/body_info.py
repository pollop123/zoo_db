from action.base import Action

class AddAnimalStateAction(Action):
    def execute(self, db_utils, **kwargs):
        a_id = kwargs.get('a_id')
        weight = kwargs.get('weight')
        user_id = kwargs.get('user_id')
        state_id = kwargs.get('state_id', 1) # Default to 1 (Normal)
        
        success, msg = db_utils.add_animal_state(a_id, weight, user_id, state_id)
        return {"success": success, "message": msg}
