from action.base import Action


class AddEmployeeSkillAction(Action):
    def execute(self, db_utils, **kwargs):
        target_e_id = kwargs.get("target_e_id")
        skill_name = kwargs.get("skill_name")

        success, msg = db_utils.add_employee_skill(target_e_id, skill_name)
        return {"success": success, "message": msg}
