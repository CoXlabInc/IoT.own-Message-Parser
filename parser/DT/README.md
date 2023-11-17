# Message Format

## D100

All values are integers with LSB first.

### Fire detector mode (```FPort``` = 1)

|Flags|Sense Time (UTC epoch)|Temperature (1/100 ℃)|Relative Humidity (1/100 %)|Fire Value (%)|Fire Alarm Threshold (%)|Battery Voltage (mV)|Report Period (sec)|
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|1-byte|4-byte|2-byte<br>(signed)|2-byte|2-byte|2-byte|2-byte|2-byte|

### Float sensor mode (```FPort``` = 2)

|Flags|Sense Time (UTC epoch)|Battery Voltage (mV)|Report Period (sec)|
|:---:|:---:|:---:|:---:|
|1-byte|4-byte|2-byte|2-byte|

### UART bridge mode (```FPort``` = 3)

|Sense Time (UTC epoch)|Report Period (sec)|Message|
|:---:|:---:|:---:|
|4-byte|2-byte|Variable length|

### Manhole sensor mode (```FPort``` = 4)

|Sense Time (UTC epoch)|Report Period (sec)|Battery Voltage (mV)|Depth to Water (mm)|Distance to Cover (mm)|
|:---:|:---:|:---:|:---:|:---:|
|5-byte|2-byte|2-byte|2-byte|2-byte|

### Landslide sensor mode (```FPort``` = 5)

|Sense Time (UTC epoch)|Report Period (sec)|Battery Voltage (mV)|X-axis Acceleration (1/1024 g)|Y-axis Acceleration (1/1024 g)|Z-axis Acceleration (1/1024 g)|Crack Value (mV)|Upper Soil Moisture (%)|Lower Soil Moisture (%)|Soil Temperature (℃)|Latitude (1/10,000,000°)|Longitude (1/10,000,000°)|Altitude (mm)|
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|5-byte|2-byte|2-byte|2-byte<br>(signed)|2-byte<br>(signed)|2-byte<br>(signed)|2-byte|Optional 2-byte|Optional 2-byte|Optional 2-byte|Optional 4-byte<br>(signed)|Optional 4-byte<br>(signed)|Optional 4-byte<br>(signed)|

If the length is 15, there are no optional fields.

If the length is 15+6 (21), it includes the soil sensor values (upper / lower soil moisture, and temperature).

If the length is 15+12 (27), it includes the GNSS location values (latitude, longitude, and altitue).

If the length is 15+6+12 (33), it includes all fields.
