from action.base import Action

class LoginAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        password = kwargs.get('password')
        success, name, role, msg = db_utils.login(e_id, password)
        return {
            "success": success,
            "name": name,
            "role": role,
            "message": msg
        }

class LogoutAction(Action):
    def execute(self, db_utils, **kwargs):
        # Server side might not need to do much for logout in this stateless-ish design,
        # but we can log it if needed.
        return {"success": True, "message": "Logged out"}

class ForgotPasswordAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        name, password, error = db_utils.get_employee_password(e_id)
        if error:
            return {"success": False, "message": error}
        return {
            "success": True,
            "name": name,
            "password": password
        }
