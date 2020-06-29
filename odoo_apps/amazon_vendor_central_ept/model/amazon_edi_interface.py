from odoo import models,fields,api,_
from odoo.osv import expression,osv
from odoo.exceptions import Warning
from ftplib import FTP
from tempfile import NamedTemporaryFile
import time
import paramiko


class AmazonEDIInterface(object):
    """
    A class to represent an FTP connection to the Amazon EDI FTP location. This is
    mostly written as an abstraction around :py:mod:`~ftplib`.

    :param host: Hostname of the Amazon EDI server
    :param user: Username for accessing the FTP share
    :param passwd: Password for the FTP share
    :param from_NETPOS_dir: Name of the direcory from which files need to be
                         imported
    :param to_NETPOS_dir: Name of the directory to which files need to be
                       uploaded
    """

    client = None

    def __init__(self, host, user, passwd, key_filename, upload_dir='',download_dir=''):
        try:
            self.host, self.port = host.split(':')
            self.port = int(self.port)
        except ValueError:
            self.host, self.port = host, 2222
        self.user = user
        self.passwd = passwd
        self.ssh = paramiko.SSHClient()
#        self.client = FTP(self.host)
        self.upload_dir = upload_dir
        self.download_dir = download_dir
        self.key_filename = key_filename
        self.__enter__()


    def __enter__(self):
        #print 'hello'
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(hostname=self.host, port=self.port or 2222, username=self.user, password = self.passwd, key_filename=self.key_filename,)
        except Exception as  e:
            raise osv.except_osv(_('Amazon EDI Error'), _('%s'%(e)))
        self.sftp_client = self.ssh.open_sftp()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.sftp_client.close()
        self.ssh.close()

    def _push_to_ftp(self, filename, file):
        """
        Uploads the given file in a binary transfer mode to the `to_dir`

        :param filename: filename of the created file
        :param file: An open file or a file like object
        """
        self.sftp_client.chdir(self.upload_dir)
        self.sftp_client.storbinary('STOR %s' % filename, file)

    def push_to_ftp(self, filename, local_file):
        """
        Uploads the given file in a binary transfer mode to the `upload_dir`

        :param filename: filename of the created file
        :param file: Path to the file name of the local file
        """
        try:
            #assert isinstance(local_file, basestring), "Local file must be a filename"

            self.sftp_client.chdir(self.upload_dir)
#             normal = self.sftp_client.normalize(remote_path)
#             remote_full_path = remote_path + '/'+filename if remote_path else ''
            s = self.sftp_client.put(local_file, filename,confirm=False)
#             print "success"+ str(s)
        except Exception as e:
            raise osv.except_osv(_('Amazon EDI Error'), _('%s'%(e)+' or  Invalide directory name. '),)

    def pull_from_ftp(self, pattern):
        """
        Pulls all the available files from the FTP location and imports them
        :param pattern: Filename Pattern to match, e.g., `Cdeclient`
        :return: Filenames of files to export
        """

        self.sftp_client.chdir(self.download_dir)

        # Match the pattern in each filename in the directory and filter
        matched_files = [f for f in self.sftp_client.listdir() if pattern in f]

        files_to_export = {}

        for file_to_import in matched_files:
            # NamedTemporaryFile is used because they have a name
            # Hence their names need to be tranferred from one method
            # to another.
            # In case of cStringIO, we would have to transfer files over
            file = NamedTemporaryFile(delete=False)
#            self.client.retrbinary('RETR %s' %file_to_import, file.write)
            file.close()

            self.sftp_client.get(file_to_import, file.name)

            files_to_export.update({file_to_import: file.name})

        return files_to_export


    def delete_from_ftp(self, filenm):
#         self.sftp_client.chdir(self.download_dir)
        self.sftp_client.remove(filenm)
        return True
