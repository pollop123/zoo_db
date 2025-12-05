from action.base import Action

class GetAnimalDietAction(Action):
    def execute(self, db_utils, **kwargs):
        species = kwargs.get('species')
        data = db_utils.get_animal_diet(species)
        return {"success": True, "data": data}

class GetAllDietSettingsAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_all_diet_settings()
        return {"success": True, "data": data}

class AddDietAction(Action):
    def execute(self, db_utils, **kwargs):
        species = kwargs.get('species')
        f_id = kwargs.get('f_id')
        success, msg = db_utils.add_diet(species, f_id)
        return {"success": success, "message": msg}

class RemoveDietAction(Action):
    def execute(self, db_utils, **kwargs):
        species = kwargs.get('species')
        f_id = kwargs.get('f_id')
        success, msg = db_utils.remove_diet(species, f_id)
        return {"success": success, "message": msg}

class GetAllSpeciesAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_all_species()
        return {"success": True, "data": data}

class GetAllFeedsAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_all_feeds()
        return {"success": True, "data": data}
