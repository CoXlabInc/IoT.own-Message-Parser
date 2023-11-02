import base64
from datetime import datetime, timedelta

TAG = 'HVT'

EVENT_PROPERTY_NAMES = [ "Ambient_Temp",
                         "Surface_Temp",
                         "Ambient_Pressure",
                         "Ambient_Humidity",
                         "Battery",
                         "Vib_Accel_X_Axis",
                         "Vib_Accel_Y_Axis",
                         "Vib_Accel_Z_Axis",
                         "Vib_Velocity_X_Axis",
                         "Vib_Velocity_Y_Axis",
                         "Vib_Velocity_Z_Axis",
                         "Audio"];

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None or message['meta'].get('fPort') is None:
        print(f'[{TAG}] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]} <= meta:{message.get("meta")})')
        
        return message

    byte = base64.b64decode(message['meta']['raw'])
    pktTime = (byte[3] << 24) | (byte[2] << 16) | (byte[1] << 8) | byte[0]
    pktTime = datetime.utcfromtimestamp(pktTime).isoformat() + 'Z'

    if message['meta']['fPort'] == 2: # Periodic measurements
        GCONVERSION = 9.8

        for i in range(4, 10):
            if byte[i] > 127:
                byte[i] = (256 - byte[i]) * (-1)

        Ambient_Temp_Max = byte[4]
        Ambient_Temp_Min = byte[5]
        Ambient_Temp_Avg = byte[6]
        Surface_Temp_Max = byte[7]
        Surface_Temp_Min = byte[8]
        Surface_Temp_Avg = byte[9]
        Ambient_Pressure_Max = (byte[10] * 3) + 300
        Ambient_Pressure_Min = (byte[11] * 3) + 300
        Ambient_Pressure_Avg = (byte[12] * 3) + 300
        Ambient_Humidity_Max = byte[13]
        Ambient_Humidity_Min = byte[14]
        Ambient_Humidity_Avg = byte[15]
        Vib_Accel_X_Axis_Max = byte[16] /GCONVERSION
        Vib_Accel_X_Axis_Min = byte[17] /GCONVERSION
        Vib_Accel_X_Axis_RMS = byte[18] /GCONVERSION
        Vib_Accel_Y_Axis_Max = byte[19] /GCONVERSION
        Vib_Accel_Y_Axis_Min = byte[20] /GCONVERSION
        Vib_Accel_Y_Axis_RMS = byte[21] /GCONVERSION
        Vib_Accel_Z_Axis_Max = byte[22] /GCONVERSION
        Vib_Accel_Z_Axis_Min = byte[23] /GCONVERSION
        Vib_Accel_Z_Axis_RMS = byte[24] /GCONVERSION
        Vib_Velocity_X_Axis_Max = byte[25]/10 # mm/sec with factor 10 from device
        Vib_Velocity_X_Axis_Min = byte[26]/10
        Vib_Velocity_X_Axis_RMS = byte[27]/10
        Vib_Velocity_Y_Axis_Max = byte[28]/10
        Vib_Velocity_Y_Axis_Min = byte[29]/10
        Vib_Velocity_Y_Axis_RMS = byte[30]/10
        Vib_Velocity_Z_Axis_Max = byte[31]/10
        Vib_Velocity_Z_Axis_Min = byte[32]/10
        Vib_Velocity_Z_Axis_RMS = byte[33]/10
        Audio_dBSPL = byte[34]
        Audio_Max = byte[35]
        Audio_Min = byte[36]
        Remaining_battery_perc = byte[37]

        message['data'] = {
            'timestamp': pktTime,
            'var_Ambient_Temp_Max': Ambient_Temp_Max,
            'var_Ambient_Temp_Min': Ambient_Temp_Min,
            'var_Ambient_Temp_Avg': Ambient_Temp_Avg,
            'var_Surface_Temp_Max': Surface_Temp_Max,
            'var_Surface_Temp_Min': Surface_Temp_Min,
            'var_Surface_Temp_Avg': Surface_Temp_Avg,
            'var_Ambient_Pressure_Max': Ambient_Pressure_Max,
            'var_Ambient_Pressure_Min': Ambient_Pressure_Min,
            'var_Ambient_Pressure_Avg': Ambient_Pressure_Avg,
            'var_Ambient_Humidity_Max': Ambient_Humidity_Max,
            'var_Ambient_Humidity_Min': Ambient_Humidity_Min,
            'var_Ambient_Humidity_Avg': Ambient_Humidity_Avg,
            'var_Vib_Accel_X_Axis_Max': Vib_Accel_X_Axis_Max,
            'var_Vib_Accel_X_Axis_Min': Vib_Accel_X_Axis_Min,
            'var_Vib_Accel_X_Axis_RMS': Vib_Accel_X_Axis_RMS,
            'var_Vib_Accel_Y_Axis_Max': Vib_Accel_Y_Axis_Max,
            'var_Vib_Accel_Y_Axis_Min': Vib_Accel_Y_Axis_Min,
            'var_Vib_Accel_Y_Axis_RMS': Vib_Accel_Y_Axis_RMS,
            'var_Vib_Accel_Z_Axis_Max': Vib_Accel_Z_Axis_Max,
            'var_Vib_Accel_Z_Axis_Min': Vib_Accel_Z_Axis_Min,
            'var_Vib_Accel_Z_Axis_RMS': Vib_Accel_Z_Axis_RMS,
            'var_Vib_Velocity_X_Axis_Max': Vib_Velocity_X_Axis_Max,
            'var_Vib_Velocity_X_Axis_Min': Vib_Velocity_X_Axis_Min,
            'var_Vib_Velocity_X_Axis_RMS': Vib_Velocity_X_Axis_RMS,
            'var_Vib_Velocity_Y_Axis_Max': Vib_Velocity_Y_Axis_Max,
            'var_Vib_Velocity_Y_Axis_Min': Vib_Velocity_Y_Axis_Min,
            'var_Vib_Velocity_Y_Axis_RMS': Vib_Velocity_Y_Axis_RMS,
            'var_Vib_Velocity_Z_Axis_Max': Vib_Velocity_Z_Axis_Max,
            'var_Vib_Velocity_Z_Axis_Min': Vib_Velocity_Z_Axis_Min,
            'var_Vib_Velocity_Z_Axis_RMS': Vib_Velocity_Z_Axis_RMS,
            'var_Audio_Max': Audio_Max,
            'var_Audio_Min': Audio_Min,
            'var_Audio_dBSPL': Audio_dBSPL,
            'var_Remaining_battery_perc': Remaining_battery_perc,
        }

    elif message['meta']['fPort'] == 8:  # Events
        decoded_8 = {
            'timestamp': pktTime,
        };

        Sensor_Type = byte[4];
        Event_Type = byte[5];

        if Sensor_Type < 4: #Regular Sensor measurement alarms
            Event_Data = byte[6]
            if Sensor_Type <= 1: #Ambient Temp, Surface Temp
                if Event_Data > 127:
                    Event_Data = (256 - byte[6])*(-1)
            elif Sensor_Type == 2: #Ambient Pressure
                Event_Data = ((byte[6] * 3) + 300);
            decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Type"] = Event_Type
            decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Data"] = Event_Data
            message['data'] = decoded_8
        elif Sensor_Type > 4 and Sensor_Type <= 11: #Vibration & Acoustics alarms
            Freq_Band = byte[7]
            Freq_Value = (byte[10] << 16) | (byte[9] << 8) | byte[8]
            Amplitude = byte[11]
            if Sensor_Type != 11: #acoustics doesn't have factor 10 for amplitude
                Amplitude = Amplitude/10;
            decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Type"] = Event_Type
            decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Freq" + Freq_Band] = Freq_Value
            decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Amp" + Freq_Band] = Amplitude
            message['data'] = decoded_8
        elif Sensor_Type == 4: #Battery Alarm
            decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Type"] = Event_Type

            if Event_Type == 1: #Battery Voltage Low
                decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Voltage"] = 3 + (byte[6] * 0.004)
            elif Event_Type == 2: #Battery Life Changed
                decoded_8["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Life"] = byte[6]
            message['data'] = decoded_8
            
    elif message['meta']['fPort'] == 11: # Diagnostics
        Diag_Status = byte[5] << 8 | byte[4]
        decoded_11 = {
            'timestamp': pktTime,
            'Diag_Status': Diag_Status,
        }

        # all measurements
        for Sensor_Type in range(0, 12):
            decoded_11["event_" + EVENT_PROPERTY_NAMES[Sensor_Type] + "_Type"] = byte[Sensor_Type + 6]
    
        message['data'] = decoded_11;
    else:
        print(f"[{TAG}] unknown format ({message['meta']['fPort']}, {len(byte)})")

    return message
