"""
Contains Qt-widgets to visualize measurements.
"""

import math
import time
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QPointF
from PyQt5.QtGui import QPen, QBrush, QPolygonF, QLinearGradient, QColor, QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsTextItem
from domain.model import Measurement


def deg2rad(degree):
    """
    :param degree: angle in degree
    :return: angle in radians
    """
    return degree * math.pi / 180.0


def rad2deg(rad):
    """
    :param rad: angle in radians
    :return: angle in degree
    """
    return rad / math.pi * 180.0


def scale(input_interval, output_interval, value):
    """
        For two intervals (input and output)
        Scales a specific value linear from [input_min, input_max] to [output_min, output_max].
    """
    min_to, max_to = output_interval
    min_from, max_from = input_interval
    mapped_value = min_to + (max_to - min_to) * ((value - min_from) / (max_from - min_from))
    return mapped_value


class RadarWidget(QWidget):
    """
    Widget to visualize Measurements in a radar like matter.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        width, height = 800, 800
        self.setGeometry(width, height, width, height)

        # configs, can be changed at runtime
        self.circle_line_color = Qt.gray
        self.crosshair_line_color = Qt.gray
        self.text_label_color = Qt.darkGreen
        self.measured_distances_color = Qt.green
        self.circle_count = 10
        self.dot_width = 10
        self.line_width = 1
        self.distance_measurement_angle = 15
        self.measurement_angle = 10  # degrees that one sensor covers
        self.fade_out_time = 4  # older measurements will fade out over this time
        self.add_text_labels = False

        # data
        self.measurements = []
        self.added_time = dict()  # measurement -> timestamp

        # drawing timer
        self.timer = QTimer()
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.draw_radar)
        self.timer.start()

        # internal canvas setup
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, width, height)
        self.canvas = QGraphicsView()
        self.canvas.setRenderHint(QPainter.Antialiasing)
        self.canvas.setFixedSize(width, height)
        self.canvas.setAlignment(Qt.AlignLeft)
        self.canvas.setScene(self.scene)
        self.canvas.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.canvas.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.canvas)

        # initial rendering
        self.draw_radar()

    @pyqtSlot(Measurement)
    def on_new_measurement(self, measurement):
        # add measurement and memorize added time
        self._purge_old_measurements()

        self.measurements.append(measurement)
        self.added_time[measurement] = time.time()

        self.draw_radar()

    @pyqtSlot()
    def draw_radar(self):
        """
        Discards the current content and redraws all elements on the graphic scene.
        """

        # decide which color to use
        bg_color, line_color = Qt.black, Qt.green

        self.scene.clear()
        self.scene.addRect(0, 0, self.width(), self.height(), brush=QBrush(bg_color))
        self._add_crosshair()
        self._add_circles(self.circle_count, self.add_text_labels)

        # for each measurement, draw a line
        for measurement in self.measurements:
            assert isinstance(measurement, Measurement)
            added_time = self.added_time[measurement]
            self._add_measurement(measurement.distance, measurement.angle, added_time)

        # for the latest 2 measurements, draw an angle visualizer
        for measurement in self.measurements[-2:]:
            self._add_latest_input_line(measurement.angle)

    @pyqtSlot()
    def clear_measurements(self):
        """Deletes all previous measurements"""
        self.measurements = []

    def _purge_old_measurements(self):
        """Removes measurements that are older than the fade_out_time"""
        min_time = time.time() - self.fade_out_time
        to_delete = [measurement for measurement in self.measurements if measurement not in self.added_time or self.added_time[measurement] < min_time]
        self.measurements = [measurement for measurement in self.measurements if measurement not in to_delete]

    def _add_latest_input_line(self, angle):
        """Adds a line to the graphic scene that visualizes a scanned angle"""
        mx, my = self._get_middle()
        angle_rad = deg2rad(angle)
        angle_1_rad = deg2rad(angle - self.measurement_angle/2.0)
        angle_2_rad = deg2rad(angle + self.measurement_angle/2.0)
        length = max(self.width(), self.height())

        start_point = (mx, my)
        p1 = (mx + length * math.cos(angle_1_rad), my + length * math.sin(angle_1_rad))
        p2 = (mx + length * math.cos(angle_2_rad), my + length * math.sin(angle_2_rad))

        gradient_start_point, gradient_end_point = (mx, my), (mx + length * math.cos(angle_rad), my + length * math.sin(angle_rad))
        gradient = QLinearGradient(*gradient_start_point, *gradient_end_point)
        gradient.setColorAt(0, Qt.transparent)
        gradient.setColorAt(0.8, Qt.red)
        gradient.setColorAt(1, Qt.darkRed)

        triangle = QPolygonF()
        triangle.append(QPointF(*start_point))
        triangle.append(QPointF(*p1))
        triangle.append(QPointF(*p2))
        triangle.append(QPointF(*start_point))

        self.scene.addPolygon(triangle, pen=QPen(Qt.transparent), brush=QBrush(gradient))

    def _get_middle(self):
        """
        returns a 2-tuple representing the middle coordinates from the upper left corner
        :return: x,y
        """
        return self.width()/2, self.height()/2

    def _add_measurement(self, length, angle, added_time):
        """
        Adds a visualization for a measured distance to the scene
        :param length: length in cm
        :param angle: the angle
        """
        mx, my = self._get_middle()
        angle_rad = deg2rad(angle)
        ex, ey = mx + length * math.cos(angle_rad), my + length * math.sin(angle_rad)

        age = time.time() - added_time
        age = age if age < self.fade_out_time else self.fade_out_time
        alpha_channel_value = scale((0, self.fade_out_time), (255, 0), age)
        assert 0 <= alpha_channel_value <= 255

        brush_color = QColor(self.measured_distances_color)
        brush_color.setAlpha(alpha_channel_value)
        brush = QBrush(brush_color)
        tpen = QPen(brush_color)

        self.scene.addLine(mx, my, ex, ey, pen=tpen)
        self.scene.addEllipse(ex-self.dot_width/2, ey-self.dot_width/2, self.dot_width, self.dot_width, pen=tpen, brush=brush)

    def _add_crosshair(self):
        """
        Adds vertical, horizontal and diagonal crosshairs to the graphic scene
        """
        pen = QPen(self.crosshair_line_color)
        pen.setWidth(self.line_width)
        pen.setStyle(Qt.DotLine)
        width, height = self.width(), self.height()
        mx, my = self._get_middle()

        # horizontal
        self.scene.addLine(0, my, width, my, pen=pen)
        # vertical
        self.scene.addLine(mx, 0, mx, height, pen=pen)
        # 45°
        self.scene.addLine(0, 0, width, height, pen=pen)
        self.scene.addLine(width, 0, 0, height, pen=pen)

    def _add_circles(self, n, add_text_labels=True):
        """
        Adds n circles to the graphic scene.
        :param n: the number of circles
        """
        pen = QPen(self.circle_line_color)
        pen.setStyle(Qt.DotLine)
        pen.setWidth(self.line_width)
        width, height = self.width(), self.height()
        stepw, steph = width/n, height/n
        mx, my = self._get_middle()

        for i in range(1, n+1):
            w, h = width - i * stepw, height - i * steph
            self.scene.addEllipse((width-w)/2, (height-h)/2, w, h, pen)

            if add_text_labels:
                text = QGraphicsTextItem()
                text.setDefaultTextColor(self.text_label_color)
                text.setPlainText(str(int(w/2)))
                text.setPos(mx+w/2.0, my)

                text2 = QGraphicsTextItem()
                text2.setDefaultTextColor(self.text_label_color)
                text2.setPlainText(str(int(-w / 2)))
                text2.setPos(mx - w / 2.0, my)

                self.scene.addItem(text)
                self.scene.addItem(text2)
