from PyQt5.QtWidgets import *
from PyQt5 import QtOpenGL, QtCore
from OpenGL.GL import *
from PyQt5.QtGui import *
from hetool.include.hetool import Hetool
from model import AppCurveCollector

class AppCanvas(QtOpenGL.QGLWidget):
    def __init__(self):
        super(AppCanvas, self).__init__()
        self.m_w = 0
        self.m_h = 0
        self.m_L = -200.0
        self.m_R = 200.0
        self.m_B = -200.0
        self.m_T = 200.0
        self.m_collector = AppCurveCollector()
        self.m_state = "View"
        self.m_mousePt = QtCore.QPointF(0.0, 0.0)
        self.m_heTol = 10.0
        self.m_step = 10
        self.meshPoints = []
        self.emitters = []
        self.restraints = []
        self.temperatures = []

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def resizeGL(self, _w, _h):
        self.m_w = _w
        self.m_h = _h

        if Hetool.isEmpty():
            self.scaleWorldWindow(1.0)
        else:
            self.fitWorldToViewport()

        glViewport(0, 0, _w, _h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        glShadeModel(GL_SMOOTH)
        patches = Hetool.getPatches()
        for patch in patches:
            if patch.isDeleted:
                glColor3f(1.0, 1.0, 1.0)
            elif patch.isSelected():
                glColor3f(1.00, 0.75, 0.75)
            else:
                glColor3f(0.75, 0.75, 0.75)

            triangs = Hetool.tessellate(patch)
            for triangle in triangs:
                glBegin(GL_TRIANGLES)
                for pt in triangle:
                    glVertex2d(pt.getX(), pt.getY())
                glEnd()

        segments = Hetool.getSegments()
        for segment in segments:
            pts = segment.getPointsToDraw()
            if segment.isSelected():
                glColor3f(1.0, 0.0, 0.0)
            else:
                glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_LINE_STRIP)
            for pt in pts:
                glVertex2f(pt.getX(), pt.getY())
            glEnd()

        points = Hetool.getPoints()
        for point in points:
            if self.checkIfPointIsInList([point.getX(), point.getY()], self.emitters):
                glColor3f(0.0, 1.0, 0.0)
            elif self.checkIfPointIsInList([point.getX(), point.getY()], self.restraints):
                glColor3f(0.0, 1.0, 1.0)
            elif self.checkIfPointIsInList([point.getX(), point.getY()], self.temperatures):
                glColor3f(1.0, 0.0, 1.0)
            else:
                if point.isSelected():
                    glColor3f(1.0, 0.0, 0.0)
                else:
                    glColor3f(0.0, 0.0, 0.0)
            glPointSize(3)
            glBegin(GL_POINTS)
            glVertex2f(point.getX(), point.getY())
            glEnd()

        if self.m_collector.isActive():
            tempCurve = self.m_collector.getCurveToDraw()
            if len(tempCurve) > 0:
                glColor3f(0.0, 0.0, 1.0)
                glBegin(GL_LINE_STRIP)
                for pti in tempCurve:
                    glVertex2f(pti[0], pti[1])
                glEnd()

    def fitWorldToViewport(self):
        if Hetool.isEmpty():
            return

        self.m_L, self.m_R, self.m_B, self.m_T = Hetool.getBoundBox()
        self.scaleWorldWindow(1.1)

    def checkIfPointIsInList(self, pt, list):
        for elem in list:
            if pt[0] == elem[0] and pt[1] == elem[1]:
                return True
        return False

    def scaleWorldWindow(self, _scaleFactor):
        cx = 0.5*(self.m_L + self.m_R)
        cy = 0.5*(self.m_B + self.m_T)
        dx = (self.m_R - self.m_L)*_scaleFactor
        dy = (self.m_T - self.m_B)*_scaleFactor

        ratioVP = self.m_h/self.m_w
        if dy > dx*ratioVP:
            dx = dy/ratioVP
        else:
            dy = dx*ratioVP

        self.m_L = cx - 0.5*dx
        self.m_R = cx + 0.5*dx
        self.m_B = cy - 0.5*dy
        self.m_T = cy + 0.5*dy

        self.m_heTol = 0.005*(dx+dy)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def setState(self, _state, _varg="default"):
        self.m_collector.deactivateCollector()
        if _state == "View":
            self.m_state = "View"
            Hetool.unSelectAll()
        elif _state == "Collect":
            self.m_state = "Collect"
            self.m_collector.activateCollector(_varg)
        elif _state == "Select":
            self.m_state = "Select"
        else:
            self.m_state = "View"

    def mouseMoveEvent(self, _event):
        pt = _event.pos()
        self.m_mousePt = pt
        if self.m_collector.isActive():
            pt = self.convertPtCoordsToUniverse(pt)
            self.m_collector.update(pt.x(), pt.y())
            self.update()

    def mouseReleaseEvent(self, _event):
        pt = _event.pos()
        if self.m_collector.isActive():
            pt_univ = self.convertPtCoordsToUniverse(pt)
            snaped, xs, ys = Hetool.snapToPoint(
                pt_univ.x(), pt_univ.y(), self.m_heTol)
            if snaped:
                isComplete = self.m_collector.collectPoint(xs, ys)
            else:
                snaped, xs, ys = Hetool.snapToSegment(
                    pt_univ.x(), pt_univ.y(), self.m_heTol)
                if snaped:
                    isComplete = self.m_collector.collectPoint(xs, ys)
                else:
                    isComplete = self.m_collector.collectPoint(
                        pt_univ.x(), pt_univ.y())

            if isComplete:
                self.setMouseTracking(False)
                curve = self.m_collector.getCurve()
                heSegment = []
                for pt in curve:
                    heSegment.append(pt[0])
                    heSegment.append(pt[1])
                Hetool.insertSegment(heSegment)
                self.update()
            else:
                self.setMouseTracking(True)

        if self.m_state == "Select":
            pt_univ = self.convertPtCoordsToUniverse(pt)
            Hetool.selectPick(pt_univ.x(), pt_univ.y(), self.m_heTol)
            self.update()
            

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scaleWorldWindow(0.9)
        else:
            self.scaleWorldWindow(1.1)
        self.update()

    def convertPtCoordsToUniverse(self, _pt):
        dX = self.m_R-self.m_L
        dY = self.m_T-self.m_B
        mX = _pt.x() * dX / self.m_w
        mY = (self.m_h-_pt.y()) * dY / self.m_h
        x = self.m_L + mX
        y = self.m_B + mY
        return QtCore.QPointF(x, y)
    
    def update_variable(self, value):
        self.m_step = int(value)
        self.update()

    def setMeshPoints(self, meshPoints):
        self.meshPoints = meshPoints
        self.update()

    def setEmitters(self, emitters):
        self.emitters = emitters
        self.update()

    def setRestraints(self, restraints):
        self.restraints = restraints
        self.update()

    def setTemperatures(self, temperatures):
        self.temperatures = temperatures
        self.update()