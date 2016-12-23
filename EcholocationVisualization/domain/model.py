"""
This module contains domain models.
"""


class Measurement:
    """
    Abstraction of a measurement
    """

    def __init__(self, angle, distance):
        """
        :param angle: the measured angle
        :param distance: the distance measured in cm
        """
        self._angle = angle
        self._distance = distance

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Angle should be numerical.")
        self._angle = value

    @property
    def distance(self):
        return self._distance

    @distance.setter
    def distance(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Distances should be numerical.")
        self._distance = value
