from action.base import Action

class GetEmployeeScheduleAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        data = db_utils.get_employee_schedule(e_id)
        return {"success": True, "data": data}

class GetMyAnimalsAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        data = db_utils.get_my_animals(e_id)
        return {"success": True, "data": data}

class AssignTaskAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        t_id = kwargs.get('t_id')
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        a_id = kwargs.get('a_id')
        
        success, msg = db_utils.assign_task(e_id, t_id, start_time, end_time, a_id)
        return {"success": success, "message": msg}

class GetAllTasksAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_all_tasks()
        return {"success": True, "data": data}

class GetAllAnimalsAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_all_animals()
        return {"success": True, "data": data}
