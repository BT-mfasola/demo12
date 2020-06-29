# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Software Solutions and Services
#    Copyright (C) 2012-2013 OpenERP Experts(<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# import xmlrpclib
from xmlrpc import client
import random
import csv
from suds.client import Client

class Magento(object):
	''' Add default login details here if required '''
	passwd = ''
	usr = ''
	URL = ''
	_svr = None
	token = ''
	
# 	passwd = ''
# 	usr = 'odoo_magento'
# 	URL = 'https://volotrading.com/index.php/'
# 	_svr = None
# 	token = ''

	def get_svr(self):
		if self._svr is None:
			raise Exception('Magento object requires a connection. Use the "connect" method to create it.')
		return self._svr
	svr = property(get_svr)

	def __init__(self, URL=None, usr=None, passwd=None):
		
		print("URLURLURLURL4444444444",URL,usr,passwd)
		if URL!=None:
			self.URL = URL
		if usr!=None:
			self.usr = usr
		if passwd!=None:
			self.passwd = passwd
		print(">>>>>>>>>>>>>>>>>>>>>",self.usr,self.URL,self.passwd)
		random.seed()

	def connect(self, URL=None, usr=None, passwd=None):
		print("URLURLURLURL",URL,usr,passwd)
		if URL==None:
			URL = self.URL+'api/v2_soap/?wsdl=1'
			print("URL",URL)
		if usr==None:
			usr = self.usr
		if passwd==None:
			passwd = self.passwd
		print("urllllllll",URL)
		self.client = Client(URL)
		self.token =  self.client.service.login(usr,passwd)

	def call(self, method_name, *args):
		try:
			result = self.svr.call(self.token, method_name, args)
		except xmlrpc.Fault as err:
			raise Exception(err.faultString)
			result=''
		return result
