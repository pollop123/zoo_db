from action.base import Action

class ChangePasswordAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        old_password = kwargs.get('old_password')
        new_password = kwargs.get('new_password')
        success, msg = db_utils.change_password(e_id, old_password, new_password)
        return {"success": success, "message": msg}

class GetAllEmployeesAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_all_employees()
        return {"success": True, "data": data}

class AddEmployeeAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        name = kwargs.get('name')
        role = kwargs.get('role', 'User')
        success, msg = db_utils.add_employee(e_id, name, role)
        return {"success": success, "message": msg}

class UpdateEmployeeStatusAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        status = kwargs.get('status')
        success, msg = db_utils.update_employee_status(e_id, status)
        return {"success": success, "message": msg}

class UpdateEmployeeRoleAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        role = kwargs.get('role')
        success, msg = db_utils.update_employee_role(e_id, role)
        return {"success": success, "message": msg}
