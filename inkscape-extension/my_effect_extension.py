#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [2021] [TOBIAS PFALLER], [tobias@pfaller.net]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Description of this extension
"""

import inkex
from inkex import Layer, FlowRoot, FlowRegion, FlowPara, Rectangle, PathElement
import requests as rest
import xml.etree.ElementTree as ET
from lxml import etree
import simplestyle
import ast
import subprocess
import os

class MyFirstExtension(inkex.EffectExtension):

	def effect(self):
		data = {'process':'pbmc'}
		#code = rest.get('http://localhost:6000/worker',data).text
		code = rest.get('http://cpee.org/inkscape-manager/worker',data).text
		if(code == 'terminated'):
			raise Exception('Process got terminated!')
		layer = self.svg.get_current_layer()
		layer.add(etree.fromstring(code))

if __name__ == '__main__':
    MyFirstExtension().run()
