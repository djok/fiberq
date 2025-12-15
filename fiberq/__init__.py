# -*- coding: utf-8 -*-
"""FiberQ QGIS plugin."""

def classFactory(iface):
    from .main_plugin import StuboviPlugin
    return StuboviPlugin(iface)
