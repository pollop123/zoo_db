from role.base import Role

class UserRole(Role):
    def __init__(self):
        super().__init__("User")
        self.allowed_actions = {
            "add_feeding", "add_body_info", "view_schedule", 
            "correct_my_record", "view_animal_trends", "view_reference_data",
            "get_recent_records", "login", "logout"
        }

    def can_perform(self, action_name):
        return action_name in self.allowed_actions

class AdminRole(Role):
    def __init__(self):
        super().__init__("Admin")
    
    def can_perform(self, action_name):
        # Admin can do everything
        return True
