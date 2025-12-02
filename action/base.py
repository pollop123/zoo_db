from abc import ABC, abstractmethod

class Action(ABC):
    @abstractmethod
    def execute(self, db_utils, **kwargs):
        """
        Execute the action logic.
        :param db_utils: Instance of DB_utils to interact with database.
        :param kwargs: Arguments required for the action.
        :return: Dictionary containing the result (success, message, data, etc.)
        """
        pass
