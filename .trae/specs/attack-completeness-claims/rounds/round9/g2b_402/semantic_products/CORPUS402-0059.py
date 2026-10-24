# Source Generated with Decompyle++ (Python version)
# File: request_utils.pyc (Python 3.11)

import subprocess
from IQCommon.common.config import FILE_SYNC_CHECK, LOCAL_IP, MASTER_IP, MASTER_PORT, MASTER_USER, SLAVE_IP, SLAVE_PORT, SLAVE_USER
from IQCommon.logger import system_log
def execute_ssh_command(ip, user, port, command):
    """通过SSH在远程服务器上执行命令并返回结果和错误码(需要服务器间配置免密)

    :param ip: str
        远程服务器IP地址
    :param user: str
        远程服务器用户名
    :param port: int
        SSH连接端口号
    :param command: str
        要在远程服务器上执行的命令
    :return: tuple
        包含返回码、标准输出和错误输出的元组 (returncode, stdout, stderr)
    """
    ssh_command = "ssh -o StrictHostKeyChecking=no -p {} {}@{} '{}'".format(port, user, ip, command)
    process = subprocess.Popen(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return (process.returncode, stdout.decode('utf8', errors='ignore'), stderr.decode('utf8', errors='ignore'))
def check_file_sync_status():
    """
    检查MASTER_IP和SLAVE_IP上指定文件是否存在，并比较文件修改时间以确保同步。
    
    :return: dict
        同步检查结果的字典，包含error_no和error_info键。
        如果检查正常，返回 {"error_no": 0, "error_info": ""}
        如果发生错误，返回 {"error_no": -1, "error_info": "错误信息"}
    """
    file_path_template = '/home/fly/nfs/notebook/backup_users/docker_usernames_{}.txt'
    master_file_path = file_path_template.format(LOCAL_IP)
    slave_file_path = file_path_template.format(LOCAL_IP)
    def file_exists_and_mod_time(ip, user, port, file_path):
        command_exists = "[ -f {} ] && echo 'exists' || echo 'not_exists'".format(file_path)
        command_mod_time = 'stat -c %Y {}'.format(file_path)
        exists_status, std_out_exists, std_err_exists = execute_ssh_command(ip, user, port, command_exists)
        if exists_status != 0 or std_out_exists.strip() == 'not_exists':
            _error_message = '{}文件不存在，无法执行文件同步检查'.format(file_path)
            return (False, _error_message, None)
        else:
            mod_time_status, std_out_mod_time, std_err_mod_time = execute_ssh_command(ip, user, port, command_mod_time)
            if mod_time_status != 0:
                _error_message = '获取{}文件修改时间失败, 错误信息: {}'.format(file_path, std_err_mod_time)
                return (False, _error_message, None)
            else:
                return (True, None, int(std_out_mod_time.strip()))
    master_exists, master_error, master_mod_time = file_exists_and_mod_time(MASTER_IP, MASTER_USER, MASTER_PORT, master_file_path)
    if not master_exists:
        system_log.error(master_error)
        return {'error_no': -1, 'error_info': master_error}
    else:
        slave_exists, slave_error, slave_mod_time = file_exists_and_mod_time(SLAVE_IP, SLAVE_USER, SLAVE_PORT, slave_file_path)
        if not slave_exists:
            system_log.error(slave_error)
            return {'error_no': -1, 'error_info': slave_error}
        elif master_mod_time - slave_mod_time > FILE_SYNC_CHECK * 60:
            error_message = '{}文件已超过{}分钟未同步，请检查实时同步服务'.format(slave_file_path, FILE_SYNC_CHECK)
            system_log.error(error_message)
            return {'error_no': -1, 'error_info': error_message}
        else:
            return {'error_no': 0, 'error_info': ''}
