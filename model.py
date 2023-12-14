import math
from PyQt5.QtWidgets import *
from OpenGL.GL import *
from PyQt5.QtGui import *

class AppCurveCollector():
    def __init__(self):
        self.m_isActive = False
        self.m_curveType = "None"
        self.m_ctrlPts = []
        self.m_tempCurve = []

    def isActive(self):
        return self.m_isActive

    def activateCollector(self, _curve):
        self.m_isActive = True
        self.m_curveType = _curve

    def deactivateCollector(self):
        self.m_isActive = False
        self.m_curveType = "None"
        self.m_ctrlPts = []
        self.m_tempCurve = []

    def collectPoint(self, _x, _y):
        isComplete = False
        if self.m_isActive:
            if self.m_curveType == "Line":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
            elif self.m_curveType == "Bezier2":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 2:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
            elif self.m_curveType == "CircleCR":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
        return isComplete

    def getCurveToDraw(self):
        return self.m_tempCurve

    def getCurve(self):
        if self.m_curveType == "Line":
            curve = self.m_ctrlPts
        else:
            curve = self.m_tempCurve
        self.m_ctrlPts = []
        self.m_tempCurve = []
        return curve

    def update(self, _x, _y):
        if self.m_curveType == "Line":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [self.m_ctrlPts[0], [_x, _y]]
        elif self.m_curveType == "Bezier2":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [self.m_ctrlPts[0], [_x, _y]]
            elif len(self.m_ctrlPts) == 2:
                nSampling = 20
                self.m_tempCurve = []
                for ii in range(nSampling+1):
                    t = ii/nSampling
                    ptx = (1-t)**2*self.m_ctrlPts[0][0] + \
                        2*(1-t)*t*_x + t**2*self.m_ctrlPts[1][0]
                    pty = (1-t)**2*self.m_ctrlPts[0][1] + \
                        2*(1-t)*t*_y + t**2*self.m_ctrlPts[1][1]
                    self.m_tempCurve.append([ptx, pty])
        elif self.m_curveType == "CircleCR":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                nSampling = 36
                self.m_tempCurve = []
                r = math.sqrt(
                    (_x-self.m_ctrlPts[0][0])**2 + (_y-self.m_ctrlPts[0][1])**2)
                for ii in range(nSampling):
                    theta = ii*(2*math.pi/nSampling)
                    ptx = self.m_ctrlPts[0][0] + r*math.cos(theta)
                    pty = self.m_ctrlPts[0][1] + r*math.sin(theta)
                    self.m_tempCurve.append([ptx, pty])
                self.m_tempCurve.append(
                    [self.m_tempCurve[0][0], self.m_tempCurve[0][1]])