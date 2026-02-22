'''
uSettings
©️ 2025 Timothy Falco
License: MIT

Dynamic settings handler developed for Falco Server. Offers an api for 
dynamic settings changes at runtime.
'''

__version__ = '1.0'

from uos import stat
from sys import print_exception
from FalcoServer import FileNotFound

class SettingType:
    ssid = 0x00
    domain = 0x01

class Settings(object):
    api = ['ssid', 'domain']
    factory_settings = ['FalcoServer', 'falco.server']
    def __init__(self):
        self.TEMPLATE_PATH = '/'
        self.xinit()
    
    def xinit(self):
        with open('/FalcoServer/uSettings/initialized.txt', 'r') as f:
            initialized = bool(int(f.read()))
        if initialized:
            return
        with open('/FalcoServer/uSettings/initialized.txt', 'w') as f:
            f.write('1')
        with open('/FalcoServer/uSettings/ssid.txt', 'w') as f:
            f.write(self.factory_settings[0])
        with open('/FalcoServer/uSettings/domain.txt', 'w') as f:
            f.write(self.factory_settings[1])
    
    def get(self, domain:str):
        '''Read a setting file by a given domain and return its 
        contents as a string.'''
        _path = f'/FalcoServer/uSettings/{domain}.txt'
        try:
            stat(_path)
            with open(_path, 'r') as f:
                x = f.read()
            return x
        except OSError:
            raise FileNotFound(_path)

    def update_setting(self, domain, new_value: str):
        '''Update a given setting by domain after diff check pass.'''
        _path = f'/FalcoServer/uSettings/{domain}.txt'
        try:
            stat(_path)
            with open(_path, 'r') as f:
                if new_value == f.read():
                    f.close()
                    return
                f.close()
            with open(_path, 'w') as f:
                f.write(new_value)
                f.close()
        except OSError:
            raise FileNotFound(_path)
    
    def new_setting(self, name: str, start_value: str):
        '''Create a new arbitrary setting file.'''
        _path = f'/FalcoServer/uSettings/{name}.txt'
        with open(_path, 'w') as f:
            f.write(start_value)
            f.close()

settings = Settings()