
import time
import logging
import base64
#from xml.dom import minidom
from lxml import etree
from copy import deepcopy

from odoo import api, fields, models, _

# import xml.etree.ElementTree as ET



from xml.dom import minidom

from datetime import date, datetime, timedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
DATE_LENGTH = len(date.today().strftime(DATE_FORMAT))
DATETIME_LENGTH = len(datetime.now().strftime(DATETIME_FORMAT))

_logger = logging.getLogger(__name__)

import xml.etree.ElementTree as ET


class ProjectNativeExchangeTool(models.TransientModel):
    _name = "project.native.exchange.tool"

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, 'utf-8', method='xml')
        reparsed = minidom.parseString(rough_string)
        ready_to = reparsed.toprettyxml(indent="\t")
        return ready_to.encode('utf-8')

    def project_date_tool(self, value=None, type_con="now", xml_datetime_format="%Y-%m-%dT%H:%M:%S"):
        """
        dateTime
        Date and time data, provided in the format YYYY-MM-DDTHH:MM:SS
        """

        if type_con == "now":
            return datetime.now().strftime(xml_datetime_format)

        if not value:
            return False

        if type_con == "to_string":

            return value.strftime(xml_datetime_format) if value else False

        if type_con == "from_string":

            value = value[:DATETIME_LENGTH]
            if len(value) == DATE_LENGTH:
                value += " 00:00:00"
            return datetime.strptime(value, xml_datetime_format)

        return False

    def xml_schedule_mode(self, value=False, direct="to_xml"):

        if not value:
            return False

        if direct == "from_xml":
            if value == "0":
                return "backward"
            if value == "1":
                return "forward"

        if direct == "to_xml":
            if value == "backward":
                return "0"
            if value == "forward":
                return "1"

        return False


    def xml_auto_manual(self, value=False, direct="to_xml"):

        if not value:
            return False

        if direct == "from_xml":
            if value == "0":
                return "auto"
            if value == "1":
                return "manual"

        if direct == "to_xml":
            if value == "auto":
                return "0"
            if value == "manual":
                return "1"

        return False

    def to_iso8601(self, value):
        # split seconds to larger units
        # PT72H0M0S
        seconds = value.total_seconds()
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        seconds = round(seconds, 6)
        seconds, hours, minutes = map(int, (seconds, hours, minutes))


        ## build time
        time = u'T'

        # hours
        bigger_exists = hours
        if bigger_exists:
            time += '{:02}H'.format(hours)

        # minutes
        bigger_exists = bigger_exists or minutes
        if bigger_exists:
            time += '{:02}M'.format(minutes)

        # seconds
        seconds = '{:02}S'.format(seconds)

        # remove trailing zeros
        seconds = seconds.rstrip('0')
        time += '{}'.format(seconds)
        return u'P' + time


    def xml_bool(self, value=None, direct="to_xml"):


        if direct == "from_xml":
            if value == "0":
                return False
            if value == "1":
                return True
            return None

        if direct == "to_xml":
            if not value:
                return "0"
            if value:
                return "1"
            return None

        return None


    # PredecessorLink - Type
    # Value Description
    # 0 FF(finish - to - finish)
    # 1 FS(finish - to - start)
    # 2 SF(start - to - finish)
    # 3 SS(start - to - start)

    # <PredecessorLink>
    #   <PredecessorUID> 192 </PredecessorUID>
    #   <Type> 1 </Type>
    #   <CrossProject> 0 </CrossProject>
    #   <LinkLag> 0 </LinkLag>
    #   <LagFormat> 7 </LagFormat>
    # </PredecessorLink>


    def xml_predecessor_type(self, value=None, direct="to_xml"):

        if value is None:
            return False

        if direct == "from_xml":
            if value == 0:
                return "FF"
            if value == 1:
                return "FS"
            if value == 2:
                return "SF"
            if value == 3:
                return "SS"

        if direct == "to_xml":
            if value == "FF":
                return "0"

            if value == "FS":
                return "1"

            if value == "SF":
                return "2"

            if value == "SS":
                return "3"

    # LagFormat
    # Format:
    # 3 m, 4 em, 35 m?, 36 em?
    # 5 h, 6 eh, 37 h?, 38 eh?
    # 7 d, 8 ed, 39 d?, 40 ed?
    # 9 w, 10 ew, 41 w?, 42 ew?
    # 11 mo, 12 emo, 43 mo?, 44 emo?
    # 19 %, 20 e%, 51 %?, 52 e%?
    # 53 null

    def xml_lag_format(self, value=None, direct="to_xml"):

        p_day = {7, 8, 39, 40}
        p_hour = {5, 6, 37, 38}
        p_minute = {3, 4, 35, 36}
        p_percent = {19, 20, 51, 52}

        if value is None:
            return False

        if direct == "from_xml":
            if value in  p_day:
                return "day"
            if value in  p_hour:
                return "hour"
            if value in  p_minute:
                return "minute"
            if value in  p_percent:
                return "percent"

        if direct == "to_xml":
            if value ==  "day":
                return "7"
            if value in  "hour":
                return "5"
            if value in  "minute":
                return "3"
            if value in  "percent":
                return "19"

    #Amount of lag time( in tenths of a minute)
    def xml_link_lag(self, value_format=False, value_data=False, direct="to_xml"):

        p_day = {7, 8, 39, 40}
        p_hour = {5, 6, 37, 38}
        p_minute = {3, 4, 35, 36}
        p_percent = {19, 20, 51, 52}

        if not value_format:
            return False

        if direct == "from_xml":
            if value_format in  p_day:
                i_value_dataint =int(value_data)
                return int(i_value_dataint / 4800)

            if value_format in  p_hour:
                i_value_dataint =int(value_data)
                return int(i_value_dataint / 1440)

            if value_format in  p_minute:
                i_value_dataint =int(value_data)
                return int(i_value_dataint / 407)
            if value_format in  p_percent:
                return int(value_data)

        if direct == "to_xml":
            if value_format ==  "day":
                return "{}".format(value_data * 4800)

            if value_format ==  "hour":
                return "{}".format(value_data * 1440)

            if value_format == "minute":
                return "{}".format(value_data * 407)

            if value_format == "percent":
                return "{}".format(value_data)



    def xml_constraint_type(self, value=None, direct="to_xml"):

        if value is None:
            return False

        if direct == "from_xml":
            if value == "0":
                return "asap"

            if value == "1":
                return "alap"

            if value == "2":
                return "mso"

            if value == "3":
                return "mfo"

            if value == "4":
                return "snet"

            if value == "5":
                return "snlt"

            if value == "6":
                return "fnet"

            if value == "7":
                return "fnlt"


        if direct == "to_xml":
            if value == "asap":
                return "0"

            if value == "alap":
                return "1"

            if value == "mso":
                return "2"

            if value == "mfo":
                return "3"

            if value == "snet":
                return "4"

            if value == "snlt":
                return "5"

            if value == "fnet":
                return "6"

            if value == "fnlt":
                return "7"