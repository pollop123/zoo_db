from abc import ABC, abstractmethod

class Role(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def can_perform(self, action_name):
        """
        Check if the role can perform the given action.
        :param action_name: Name of the action (e.g., 'add_feeding').
        :return: Boolean
        """
        pass
