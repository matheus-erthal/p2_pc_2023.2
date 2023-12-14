from PyQt5.QtWidgets import *
from OpenGL.GL import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, pyqtSignal
from hetool.include.hetool import Hetool
from hetool.compgeom.compgeom import CompGeom
from hetool.geometry.point import Point
import numpy as np
import json
from canvas import AppCanvas

class AppWindow(QMainWindow):
    def __init__(self):
        super(AppWindow, self).__init__()
        self.setGeometry(150, 100, 900, 700)
        self.setWindowTitle("Modelador - 116031025")
        self.m_canvas = AppCanvas()
        self.setCentralWidget(self.m_canvas)

        tb = self.addToolBar("ToolBar")
        fit = QAction("Fit View", self)
        tb.addAction(fit)
        addLine = QAction("Add Line", self)
        tb.addAction(addLine)
        addBezier2 = QAction("Add 3 pt Bezier", self)
        tb.addAction(addBezier2)
        addCircleCR = QAction("Add Circle", self)
        tb.addAction(addCircleCR)
        select = QAction("Select", self)
        tb.addAction(select)
        tesselation = QAction("Tesselation", self)
        tb.addAction(tesselation)
        
        tb.actionTriggered[QAction].connect(self.tbpressed)

        opengl_label = QLabel("Step:", self)
        tb.addWidget(opengl_label)
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText(str(self.m_canvas.m_step))
        self.input_field.returnPressed.connect(self.update_variable)
        tb.addWidget(self.input_field)

        selectForce = QAction("F", self)
        tb.addAction(selectForce)
        selectRestraint = QAction("R", self)
        tb.addAction(selectRestraint)
        selectTemperature = QAction("T", self)
        tb.addAction(selectTemperature)
        export_f = QAction("Exportar (F)", self)
        tb.addAction(export_f)
        export_t = QAction("Exportar (T)", self)
        tb.addAction(export_t)

        clear = QAction("Limpar", self)
        tb.addAction(clear)

    def update_variable(self):
        if self.input_field.text() == "":
            return
        try:
            self.variable_value = float(self.input_field.text())
            self.m_canvas.update_variable(self.variable_value)
        except ValueError:
            print("Digite um número válido.")

    def tbpressed(self, _action):
        if _action.text() == "Fit View":
            self.m_canvas.fitWorldToViewport()
            self.m_canvas.update()
        elif _action.text() == "Add Line":
            self.m_canvas.setState("Collect", "Line")
        elif _action.text() == "Add 3 pt Bezier":
            self.m_canvas.setState("Collect", "Bezier2")
        elif _action.text() == "Add Circle":
            self.m_canvas.setState("Collect", "CircleCR")
        elif _action.text() == "Select":
            self.m_canvas.setState("Select")
        elif _action.text() == "Tesselation":
            self.generate_mesh()
        elif _action.text() == "F":
            points = Hetool.getSelectedPoints()
            if len(points) > 0:
                self.openDialog("F")
        elif _action.text() == "R":
            points = Hetool.getSelectedPoints()
            if len(points) > 0:
                self.handleRestraint()
        elif _action.text() == "T":
            points = Hetool.getSelectedPoints()
            if len(points) > 0:
                self.openDialog("T")
        elif _action.text() == "Exportar (F)":
            self.generate_input()
        elif _action.text() == "Exportar (T)":
            self.generate_input_temperature()
        elif _action.text() == "Limpar":
            self.handleClear()

    def handleClear(self):
        Hetool.resetDataStructure()
        self.m_canvas.setEmitters([])
        self.m_canvas.setRestraints([])
        self.m_canvas.setMeshPoints([])

    def handleRestraint(self):
        points = Hetool.getSelectedPoints()
        self.m_canvas.setRestraints(self.m_canvas.restraints + [[points[0].getX(), points[0].getY()]])

    def openDialog(self, kind="F"):
        dialog = CustomDialog(self, kind)
        if kind == "F":
            dialog.values_accepted_f.connect(self.handleValuesAccepted)
        else:
            dialog.values_accepted_t.connect(self.handleValuesAcceptedTemperature)
        dialog.exec_()

    def handleValuesAccepted(self, x, y):
        points = Hetool.getSelectedPoints()
        self.m_canvas.setEmitters(self.m_canvas.emitters + [[points[0].getX(), points[0].getY(), x, y]])

    def handleValuesAcceptedTemperature(self, t):
        points = Hetool.getSelectedPoints()
        self.m_canvas.setTemperatures(self.m_canvas.temperatures + [[points[0].getX(), points[0].getY(), t]])
        print(self.m_canvas.temperatures)

    def generate_mesh(self):
        patches = Hetool.getPatches()    
        mesh = []
        for x in range(int(self.m_canvas.m_L), int(self.m_canvas.m_R), self.m_canvas.m_step):
            for y in range(int(self.m_canvas.m_B), int(self.m_canvas.m_T), self.m_canvas.m_step):
                point = Point(x, y)
                for patch in patches:
                    if CompGeom.isPointInPolygon(patch.getPoints(), point):
                        Hetool.insertPoint([x, y], 3)
                        mesh.append([x, y])
        self.m_canvas.setMeshPoints(mesh)
        self.m_canvas.update()

    def generate_connection(self, points, step):
        connections = np.zeros((len(points), 5), dtype=int)
        for i in range(len(points)):
            for j in range(i+1, len(points)):
                esquerda = (points[i][0] - step == (points[j][0])) and (points[i][1] == points[j][1])
                direita = (points[i][0] + step == (points[j][0])) and (points[i][1] == points[j][1])
                cima = (points[i][0] == (points[j][0])) and (points[i][1] - step == points[j][1])
                baixo = (points[i][0] == (points[j][0])) and (points[i][1] + step == points[j][1])
                if esquerda or direita or cima or baixo:
                    atuais_i = connections[i][0]
                    atuais_j = connections[j][0]
                    connections[i][atuais_i+1] = j + 1
                    connections[i][0] += 1
                    connections[j][atuais_j+1] = i + 1
                    connections[j][0] += 1
        return connections.tolist()
    
    def generate_connection_temperature(self, points, step):
        connections = np.zeros((len(points), 4), dtype=int)
        for i in range(len(points)):
            for j in range(len(points)):
                if i == j:
                    continue
                esquerda = (points[i][0] - step == (points[j][0])) and (points[i][1] == points[j][1])
                direita = (points[i][0] + step == (points[j][0])) and (points[i][1] == points[j][1])
                cima = (points[i][0] == (points[j][0])) and (points[i][1] - step == points[j][1])
                baixo = (points[i][0] == (points[j][0])) and (points[i][1] + step == points[j][1])
                if esquerda or direita or cima or baixo:
                    for k in range(4):
                        if connections[i][k] == j + 1:
                            break
                        if connections[i][k] == 0:
                            connections[i][k] = j + 1
                            break
                    for k in range(4):
                        if connections[j][k] == i + 1:
                            break
                        if connections[j][k] == 0:
                            connections[j][k] = i + 1
                            break
        return connections.tolist()

    def format_emitters(self, emitters, points):
        formatted_emitters = []
        for point in points:
            has_value = False
            for emitter in emitters:
                if emitter[0] == point[0] and emitter[1] == point[1]:
                    has_value = True
                    formatted_emitters.append([emitter[2], emitter[3]])
            if not has_value:
                formatted_emitters.append([0, 0])
        return formatted_emitters
    
    def format_restraints(self, restraints, points):
        formatted_restraints = []
        for point in points:
            has_value = False
            for restraint in restraints:
                if restraint[0] == point[0] and restraint[1] == point[1]:
                    has_value = True
                    formatted_restraints.append([1, 1])
            if not has_value:
                formatted_restraints.append([0, 0])
        return formatted_restraints
    
    def format_temperature(self, temperatures, points):
        formatted_temperatures = []
        for point in points:
            has_value = False
            for temperature in temperatures:
                if temperature[0] == point[0] and temperature[1] == point[1]:
                    has_value = True
                    formatted_temperatures.append([1, temperature[2]])
            if not has_value:
                formatted_temperatures.append([0, 0])
        return formatted_temperatures

    def generate_input(self):
        if len(self.m_canvas.meshPoints) == 0:
            return
        input = {}
        input["coords"] = self.m_canvas.meshPoints
        input["connections"] = self.generate_connection(self.m_canvas.meshPoints, self.m_canvas.m_step)
        input["F"] = self.format_emitters(self.m_canvas.emitters, self.m_canvas.meshPoints)
        input["restraints"] = self.format_restraints(self.m_canvas.restraints, self.m_canvas.meshPoints)
        self.write_dict_to_json(input)

    def generate_input_temperature(self):
        if len(self.m_canvas.meshPoints) == 0:
            return
        input = {}
        input["connections"] = self.generate_connection_temperature(self.m_canvas.meshPoints, self.m_canvas.m_step)
        input["T"] = self.format_temperature(self.m_canvas.temperatures, self.m_canvas.meshPoints)
        self.write_dict_to_json(input)
    
    def write_dict_to_json(self, input):
        with open('input.json', 'w') as outfile:
            json.dump(input, outfile)


class CustomDialog(QDialog):
    values_accepted_f = pyqtSignal(float, float)
    values_accepted_t = pyqtSignal(float)

    def __init__(self, parent=None, kind="F"):
        super(CustomDialog, self).__init__(parent)
        self.setWindowTitle("OpenGL Dialog")
        self.setGeometry(80, 80, 80, 80)
        
        self.kind = kind

        if kind == "F":
            self.x_label = QLabel("X:", self)
            self.y_label = QLabel("Y:", self)
            self.x_edit = QLineEdit(self)
            self.y_edit = QLineEdit(self)

            layout = QVBoxLayout(self)
            layout.addWidget(self.x_label)
            layout.addWidget(self.x_edit)
            layout.addWidget(self.y_label)
            layout.addWidget(self.y_edit)
        else:
            self.t_label = QLabel("T:", self)
            self.t_edit = QLineEdit(self)

            layout = QVBoxLayout(self)
            layout.addWidget(self.t_label)
            layout.addWidget(self.t_edit)

        self.accept_button = QPushButton("Send", self)
        self.accept_button.clicked.connect(self.acceptValues)
        layout.addWidget(self.accept_button)

    def acceptValues(self):
        if self.kind == "F":
            x_value = float(self.x_edit.text()) if self.x_edit.text() else 0.0
            y_value = float(self.y_edit.text()) if self.y_edit.text() else 0.0
            self.values_accepted_f.emit(x_value, y_value)
        else:
            t_value = float(self.t_edit.text()) if self.t_edit.text() else 0.0
            self.values_accepted_t.emit(t_value)
        self.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()