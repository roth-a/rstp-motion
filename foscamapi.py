import requests, xmltodict



class FoscamAPI():
    def __init__(self, username, password, ip, port = 88):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def url_cgi(self, data=None):
        "Data must contain the key 'cmd' "
        import urllib.parse
        if data is None:
            data = {}
        data['usr'] = self.username
        data['pwd'] = self.password         
        return f"http://{self.ip}:{self.port}/cgi-bin/CGIProxy.fcgi?{urllib.parse.urlencode(data)}"



    def _confert_dict_to_int_dict(self, d):
        def save_int(v):
            try:
                return int(v)
            except:
                return v
        return {k:save_int(v) for k,v in d.items()}
                         
    def requests_command(self, data=None, timeout=3):
        response = requests.get(self.url_cgi(data), timeout=timeout)
        doc = xmltodict.parse(response.content)  
        return self._confert_dict_to_int_dict(doc.get('CGI_Result')) if 'CGI_Result' in doc else doc
        
        

    def set_datetime(self):
        import datetime
        now = datetime.datetime.now()
        data = {'cmd':'setSystemTime',
                'timeSource':1,
                'ntpServer':'',
                'dateFormat':0,
                'timeFormat':1,
                'timeZone':0,
                'isDst':1,
                'dst':0,
                'year':now.year,
                'mon':now.month,
                'day':now.day,
                'hour':now.hour,
                'minute':now.minute,
                'sec':now.second,
                }

        try:
            res = self.requests_command(data, timeout=10)['result']
            # print(f"Answer from setting datetime: \n{res}")
            return res
        except:
            print('Could not set the time')

        
        
    def get_dev_state(self):
        return self.requests_command({'cmd':'getDevState'})
    
    def detected_sound(self, dev_state=None):
        # 0-Disabled, 1-No Alarm, 2-Detect Alarm
        dev_state = dev_state if dev_state else self.get_dev_state()
        
        state = int(dev_state['soundAlarm'])
        if state == 0:
            # print('Warning: The sound detection is disabled. No detection possible')
            return None
        return True if state == 2 else False        
    
    def detected_motion(self, dev_state=None):  
        # 0-Disabled, 1-No Alarm, 2-Detect Alarm
        dev_state = dev_state if dev_state else self.get_dev_state()

        state = int(dev_state['motionDetectAlarm'])
        if state == 0:
            print('Warning: The motion detection is disabled. No detection possible')
            return None
        return True if state == 2 else False
            
    def get_motion_detection(self):
        return bool(self.get_motion_detection_config()['isEnable'])

    def get_motion_detection_config(self):
        return self.requests_command({'cmd':'getMotionDetectConfig'})

    def set_motion_detection(self, enabled='toggle', sensitivity=1, audio_ring=None, timeout=10):
        """https://www.foscam.es/descarga/Foscam-IPCamera-CGI-User-Guide-AllPlatforms-2015.11.06.pdf
        
        sensitivity 
            0 :Low
            1: Normal
            2: High
            3: Lower
            4: Lowest
        """
        old_state = self.get_motion_detection_config()
        if enabled == 'toggle':
            enabled = not bool(old_state['isEnable'])

        enabled = bool(enabled)
        data = {
                'cmd':'setMotionDetectConfig',
                'isEnable':int(enabled),
                'linkage':old_state['linkage'] if audio_ring is None else int(audio_ring),
                'snapInterval':3,
                'sensitivity':sensitivity,
                'triggerInterval':5,
                'schedule0':281474976710655,
                'schedule1':281474976710655,
                'schedule2':281474976710655,
                'schedule3':281474976710655,
                'schedule4':281474976710655,
                'schedule5':281474976710655,
                'schedule6':281474976710655,
                'area0':1023,
                'area1':1023,
                'area2':1023,
                'area3':1023,
                'area4':1023,
                'area5':1023,
                'area6':1023,
                'area7':1023,
                'area8':1023,
                'area9':1023,
                'isMovAlarmEnable':int(enabled),
                'isPirAlarmEnable':int(enabled),
                }
    
        try: 
            return self.requests_command(data, timeout=timeout)['result']
        except:
            print('Error in set_motion_detection')
            
    def get_night_light_status(self):  
        return bool(int( self.requests_command({'cmd':'getNightLightState'})['state']))
            
    def set_night_light_status(self, enabled='toggle'):
        if enabled == 'toggle':
            enabled = not self.get_night_light_status()
        
        return self.requests_command({'cmd':'setNightLightState', 'state':int(enabled)})['result']
    
    def get_video_stream_parameters(self):
        return self.requests_command({'cmd':'getVideoStreamParam'})                                    
                 
    def get_image_setting(self):
        return self.requests_command({'cmd':'getImageSetting'}) 
                                                 
    def get_wifi_list(self):
        return self.requests_command({'cmd':'getWifiList'}) 

    def refresh_wifi_list(self):
        return self.requests_command({'cmd':'refreshWifiList'}, timeout=60) 
    
    def getwifi_config(self):
        return self.requests_command({'cmd':'getWifiConfig'}) 
    def get_port_info(self):
        return self.requests_command({'cmd':'getPortInfo'}) 
    def get_infrared_led_config(self):
        """
        0 Auto mode
        1 Manual mode
        """
        return int(self.requests_command({'cmd':'getInfraLedConfig'})['mode'])
    
    def set_infrared_led_config(self, mode='toggle'):
        """
        0 Auto mode
        1 Manual mode
        """
        if mode == 'toggle':
            mode = int(not bool(self.get_infrared_led_config()))
        assert int(mode) in [0, 1]
        return self.requests_command({'cmd':'setInfraLedConfig', 'mode':int(mode)})
    
    
    def get_infrared_led(self):
        return bool(int(self.get_dev_state()['infraLedState']))
        
    def set_infrared_led(self, enabled='toggle'):
        if enabled == 'toggle':
            enabled = not self.get_infrared_led()
            
        cmd = 'openInfraLed' if int(enabled) else 'closeInfraLed'
        result = self.requests_command({'cmd':cmd}) 
        if result.get('ctrlResult') == "-1" :
            print('Failed.  Please do:  set_infrared_led_config(1)')
        return result
            
    def get_log(self):
        return self.requests_command({'cmd':'getLog'})  
    def get_main_video_stream_type(self):
        "The stream type 0~3"
        return int(self.requests_command({'cmd':'getMainVideoStreamType'})['streamType'])
    def set_main_video_stream_type(self, value=1):
        "The stream type 0~3,  0 seems to be too high quality"
        return self.requests_command({'cmd':'setMainVideoStreamType', 'streamType':value})

    def get_video_stream_infos(self):
        info = self.get_video_stream_parameters()
        keys = ['resolution', 'bitRate', 'isVBR', 'frameRate']
        infos = [{
            key:int(info.get(f'{key}{i}')) for key in keys
        } for i in range(4)]
        return infos

    def get_main_video_stream_infos(self):
        return self.get_video_stream_infos()[self.get_main_video_stream_type()]

    def get_audio_alarm_config(self):
        return self.requests_command({'cmd':'getAudioAlarmConfig'})

    def set_audio_alarm_config(self, enabled='toggle', sensitivity=2):
        "sensitivity 0=low 1=middle 2=high"
        if enabled == 'toggle':
            enabled = not bool(self.get_audio_alarm_config()['isEnable'])
        return self.requests_command({  
                                        'cmd':'setAudioAlarmConfig', 
                                        'schedule0':281474976710655,
                                        'schedule1':281474976710655,
                                        'schedule2':281474976710655,
                                        'schedule3':281474976710655,
                                        'schedule4':281474976710655,
                                        'schedule5':281474976710655,
                                        'schedule6':281474976710655,
                                        'snapInterval':2,
                                        'linkage':0,
                                        'triggerInterval':10,
                                        'sensitivity':sensitivity, 
                                        'isEnable':int(enabled)}) 

    

