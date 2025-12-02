from action.base import Action

class LoginAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        success, name, role = db_utils.login(e_id)
        return {
            "success": success,
            "name": name,
            "role": role,
            "message": "Login successful" if success else "Login failed"
        }

class LogoutAction(Action):
    def execute(self, db_utils, **kwargs):
        # Server side might not need to do much for logout in this stateless-ish design,
        # but we can log it if needed.
        return {"success": True, "message": "Logged out"}
