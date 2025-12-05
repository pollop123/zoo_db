from action.base import Action

class CheckWeightAnomalyAction(Action):
    def execute(self, db_utils, **kwargs):
        a_id = kwargs.get('a_id')
        success, msg, pct = db_utils.check_weight_anomaly(a_id)
        return {"success": success, "message": msg, "pct": pct}

class BatchCheckAnomaliesAction(Action):
    def execute(self, db_utils, **kwargs):
        anomalies = db_utils.batch_check_anomalies()
        return {"success": True, "data": anomalies}

class GetHighRiskAnimalsAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_high_risk_animals()
        return {"success": True, "data": data}

class GetAnimalTrendsAction(Action):
    def execute(self, db_utils, **kwargs):
        a_id = kwargs.get('a_id')
        weights, feedings = db_utils.get_animal_trends(a_id)
        return {"success": True, "weights": weights, "feedings": feedings}

class GetAuditLogsAction(Action):
    def execute(self, db_utils, **kwargs):
        logs = db_utils.get_audit_logs()
        return {"success": True, "data": logs}

class GetCarelessEmployeesAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_careless_employees()
        return {"success": True, "data": data}

class GetPendingHealthAlertsAction(Action):
    def execute(self, db_utils, **kwargs):
        data = db_utils.get_pending_health_alerts()
        return {"success": True, "data": data}

class ConfirmHealthAlertAction(Action):
    def execute(self, db_utils, **kwargs):
        alert_id = kwargs.get('alert_id')
        status = kwargs.get('status')
        success, msg = db_utils.confirm_health_alert(alert_id, status)
        return {"success": success, "message": msg}

class GetMyCorrectionsAction(Action):
    def execute(self, db_utils, **kwargs):
        e_id = kwargs.get('e_id')
        data = db_utils.get_my_corrections(e_id)
        return {"success": True, "data": data}
