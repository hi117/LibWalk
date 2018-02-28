'''
This script walks all binaries and finds all libs and sees if they have been
updated since the program's start time
'''

import datetime
import subprocess
import re
import os
import os.path

def list_processes():
    '''
    Returns a list of pids on the system
    '''
    return [pid for pid in os.listdir('/proc') if pid.isdigit()]

def get_process_start_time(pid):
    '''
    Returns a datetime of the start time for a pid
    '''
    output = subprocess.check_output(['ps', '-o', 'lstart', '-q',
                                      bytes(pid, 'utf8')]).split(b'\n')[1]
    return datetime.datetime.strptime(output.decode('utf8'), '%a %b %d %H:%M:%S %Y')

def list_process_libraries(pid):
    '''
    Returns a list of full paths to libraries that the process needs
    '''
    map_parser = re.compile('[0-9a-f]+-[0-9a-f]+ r-xp [0-9a-f]+ [0-9a-f]+:[0-9a-f]+'
                            ' \\d+ +(/.*?) (\\(deleted\\))?$')
    libs = set()
    with open('/proc/{}/maps'.format(pid)) as maps:
        for line in maps:
            match = map_parser.match(line)
            if not match:
                continue
            libs.add(match.group(1))
    return libs

def get_file_mtime(path):
    '''
    Returns the mtime for a file at the given path as a datetime object
    '''
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))

def should_be_restarted(pid):
    '''
    Prints a message saying that a given pid should be restarted
    '''
    if has_systemd():
        print('{} <{}> of unit {} should be restarted'.format(os.readlink('/proc/{}/exe'.format(pid)), pid, get_systemd_unit(pid)))
    else:
        print('{} <{}> should be restarted'.format(os.readlink('/proc/{}/exe'.format(pid)), pid))

def has_systemd():
    '''
    Returns if a system has systemd
    '''
    # TODO: do actual detection
    return True

def get_systemd_unit(pid):
    '''
    Returns the unit associated with the pid
    '''
    data = subprocess.check_output(['systemctl', 'status', pid])
    return data.split(b'\n')[0].split(b' - ')[0].split(b' ')[1].decode('utf8')

def main():
    '''
    Main function for this script
    '''
    for pid in list_processes():
        try:
            start_time = get_process_start_time(pid)
        except subprocess.CalledProcessError:
            continue
        try:
            libs = list_process_libraries(pid)
        except PermissionError:
            continue
        for lib in libs:
            try:
                if get_file_mtime(lib) > start_time:
                    should_be_restarted(pid)
                    break
            except FileNotFoundError:
                should_be_restarted(pid)
                break

if __name__ == '__main__':
    main()
