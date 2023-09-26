# Sensors

| Type | Key name | Remark |
|---|---|---|
| ```0xAF``` | ```CommErr``` | ```protocol error```, ```wrong tag```, ... |
| ```0xA6``` | ```model``` | |
| ```0xA7``` | ```HardwareVersion``` | |
| ```0xA8``` | ```FirmwareVersion``` | |
| ```0xA9``` | ```ProtocolVersion``` | |
| ```0xAA``` | ```SerialNumber``` | |
| ```0xB0``` | ```LastReceived``` | |
| ```0xB1``` | ```SensorList``` | Array of attached sensors |
| ```0xB2``` | ```MeasurementTime``` | |
| ```0xB3``` | ```NumPackets``` | |
| ```0xB4``` | ```PacketIndex``` | |
| ```0xB6``` | ```Alarm_FireExtinguisher```<br>```Alarm_Fire```<br>```Alarm_ManholeInsideDoor```<br>```Alarm_WaterLevel```<br>```Alarm_ManholeOutsideDoor```<br>```Alarm_LowBattery```<br>or ```Alarm```| ```Alarm``` is used for undefined alarm |
| ```0xC1``` | ```BatteryVoltage``` | |
| ```0xC3``` | ```Status_FireExtinguisher```<br>```Status_ManholeInsideDoor```<br>```Status_ManholeOutsideDoor```<br>or ```Status``` | ```Status``` is used for undefined status |
| ```0xC6``` | ```DepthToWater``` | |
| ```0xC7``` | ```CO``` | |
| ```0xC8``` | ```CO2``` | |
| ```0xC9``` | ```CH4``` | |
| ```0xCA``` | ```O2``` | |
| ```0xCB``` | ```H2S``` | |
| ```0xCC``` | ```Temperature``` | |
| ```0xCD``` | ```Humidity``` | |
| ```0xCE``` | ```Smoke``` | |
| ```0xCF``` | ```Status_FireExtinguisher```<br>or ```Status``` | ```Status``` is used for undefined status |
| ```0xD0``` | ```H``` | |
| ```0xD1``` | ```1_DepthToWater``` | |
| ```0xD2``` | ```2_DepthToWater``` | |
| ```0xD3``` | ```3_DepthToWater``` | |
| ```0xD4``` | ```4_DepthToWater``` | |
| ```0xD5``` | ```1_SoilTemperature``` | |
| ```0xD6``` | ```1_SoilMoisture``` | |
| ```0xD7``` | ```1_SoilEC``` | |
| ```0xD8``` | ```2_SoilTemperature``` | |
| ```0xD9``` | ```2_SoilMoisture``` | |
| ```0xDA``` | ```2_SoilEC``` | |
| ```0xDB``` | ```GroundSurfaceTemperature``` | |
| ```0xDC``` | ```WindDirection``` | |
| ```0xDD``` | ```WindSpeed``` | |
| ```0xDE``` | ```AmbientTemperature``` | |
| ```0xDF``` | ```AmbientHumidity``` | |
| ```0xE0``` | ```AtmosphericPressure``` | |
| ```0xE1``` | ```Precipitation``` | |
| ```0xE2``` | ```Flux``` | |
| ```0xE3``` | ```1_Temperature``` | |
| ```0xE4``` | ```1_Humidity``` | |
| ```0xE5``` | ```Solar Radiation``` | |

# Units

The unit may follow the key name with ```_```. The unit can be one of below:

```V```, ```Kelvin```, ```%```, ```ppm```, ```cm```, ```_mS/cm```, ```hPa```, ```m/sec```, ```deg```, ```mm/h```, ```W/m^2```, ```m^3/h```
