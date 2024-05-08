// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil; -*-
/*
 * !!! IMPORTANT 1 !!!
 * Must restart IoT.own after implementing a custom handler.
 * $ sudo systemctl stop iotown
 * $ sudo systemctl start iotown
 *
 * !!! IMPORTANT 2 !!!
 * If dataHandler has an error or exception, IoT.own may be crushed.
 */

function toHexString(byteArray) {
    return Array.from(byteArray, function(byte) {
        return ('0' + (byte & 0xFF).toString(16)).slice(-2);
    }).join('')
}

exports.dataHandler = function (data, node, gateway /* <= Buffer type */) {
    var out = {};
    out.errors = '';

    var bcnum = 0;

    if(gateway != null && gateway != undefined)
        out.gateway_power = gateway.power;

    if((data[0] != 0x55) && (data[0] > 0x0F))
    {
        return out;
    }
    else
    {
        out.seq = data[0];
    }
    
    for (var i = 1; i < data.length; ) {
        const type = data[i];
        const length = data[i + 1];

        if (type == 0x00) {
            out.Status = data[i + 2];
        } else if (type == 0x01) {
            out.deviceCompanyName = data.toString('ascii', (i + 2), (i + 2 + length));
        } else if (type == 0x02) {
            out.deviceModelName = data.toString('ascii', (i + 2), (i + 2 + length));
        } else if (type == 0x03) {
            out.deviceHWVersion = data.toString('ascii', (i + 2), (i + 2 + length));
        } else if (type == 0x04) {
            out.deviceSWVersion = data.toString('ascii', (i + 2), (i + 2 + length));
        } else if (type == 0x05) {
            out.timeInfo = data.toString('ascii', (i + 2), (i + 2 + length));
        } else if (type == 0x06) {
            const val = data[i + 2];
            if (val == 0) {
                out.weekday = 'Sunday';
            } else if (val == 1) {
                out.weekday = 'Monday';
            } else if (val == 2) {
                out.weekday = 'Tuesday';
            } else if (val == 3) {
                out.weekday = 'Wednesday';
            } else if (val == 4) {
                out.weekday = 'Thursday';
            } else if (val == 5) {
                out.weekday = 'Friday';
            } else if (val == 6) {
                out.weekday = 'Saturday';
            } else {
                out.weekday = 'Unknown value: ' + val
            }
        } else if (type == 0x07) {
            var val = data[i + 2];
            switch (length)
            {
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.panID = val;
        } else if (type == 0x08) {
            var val = data[i + 2];
            switch (length)
            {
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.shortID = val;
        } else if (type == 0x09) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.companyID = val;
        } else if (type == 0x0a) {
            const val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.loraInfo = val;
        } else if (type == 0x0b) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.senCapa = val.toString(16);
        } else if (type == 0x0f) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.result = val;
        } else if (type == 0x13) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            /* out.temperature = (val/10).toString(); */
            var sign = val & (1 << 15);
            if(sign)
            {
                out.temperature = ((0xFFFF0000 | val)/10);
            }
            else
            {
                out.temperature = (val/10);
            }

        } else if (type == 0x14) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.humidity = (val/10);

        } else if (type == 0x15) {
            var val = data[i + 2];
            switch (length)
            {
                //case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                //case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            /* out.pressure = (val/10).toString(); */
            /* out.temperature = (val/10).toString(); */
            var sign = val & (1 << 15);
            if(sign)
            {
                out.pressure = ((0xFFFF0000 | val)/10).toString();
            }
            else
            {
                out.pressure = (val/10).toString();
            }

        } else if (type == 0x16) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.lux = val;

        } else if (type == 0x20) {

            //out.GPS = data.toString('ascii', (i + 2), (i + 2 + length));
            const gps = data.toString('ascii', (i + 2), (i + 2 + length));
            var lock = gps.substring(0,1);
            var lat = gps.substring(2, gps.substring(2).indexOf(",")+2);
            var idx = gps.substring(2).indexOf(",") + 2;
            var lon = gps.substring(idx+1, length);
            out.lock = parseInt(lock);

            var gnss = [];
            gnss.push(parseFloat(lat));
            gnss.push(parseFloat(lon));
            out.gnss = gnss;
            //out.gnss = [parseFloat(lat), parseFloat(lon)];

        } else if (type == 0x21) {

            const x_axis = data.toString('ascii', (i + 2), (i + 7));
            const y_axis = data.toString('ascii', (i + 8), (i + 13));
            const z_axis = data.toString('ascii', (i + 14), (i + 19));
            out.gyroGravity = x_axis + ',' + y_axis + ',' + z_axis;

        } else if (type == 0x22) {
            var s = i + 2;
            var stepc = 0;
            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    out.stepRTC = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x02) {
                    out.stepInterval = data[s + j + 2];
                }
                else if ( sub_type == 0x03) {

                    switch(stepc)
                    {
                        case 0: out.stepNum1 = (data[s + j + 2] << 8) + data[s + j + 3]; break;
                        case 1: out.stepNum2 = (data[s + j + 2] << 8) + data[s + j + 3]; break;
                        case 2: out.stepNum3 = (data[s + j + 2] << 8) + data[s + j + 3]; break;
                        case 3: out.stepNum4 = (data[s + j + 2] << 8) + data[s + j + 3]; break;
                        case 4: out.stepNum5 = (data[s + j + 2] << 8) + data[s + j + 3]; break;
                    }
                    stepc += 1;
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }
        } else if (type == 0x2B) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.pitch = val;

        } else if (type == 0x2C) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.roll = val;

        } else if (type == 0x2D) {
            var s = i + 2;
            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    out.vibSubX = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x02) {
                    out.vibSubY = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x03) {
                    out.vibSubZ = (data[s + j + 2] << 8) + data[s + j + 3];
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }

        } else if (type == 0x3A) {
            var s = i + 2;
            var major;
            var minor;
            var rssi;

            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    major = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x02) {
                    minor = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x03) {
                    var sign = data[s + j + 2] & (1 << 7);
                    if(sign)
                    {
                        rssi = (0xFFFFFF00 | data[s + j + 2]).toString();
                    }
                    else
                    {
                        rssi = data[s + j + 2].toString();
                    }
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }

            switch(bcnum)
            {
                case 0: out.beacon1Major = major;out.beacon1Minor = minor; out.beacon1Rssi = rssi; break;
                case 1: out.beacon2Major = major;out.beacon2Minor = minor; out.beacon2Rssi = rssi; break;
                case 2: out.beacon3Major = major;out.beacon3Minor = minor; out.beacon3Rssi = rssi; break;
                case 3: out.beacon4Major = major;out.beacon4Minor = minor; out.beacon4Rssi = rssi; break;
            }
            bcnum += 1;

        } else if (type == 0x3B) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }

            out.distance = val/10;

        } else if (type == 0x3F) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
            }

            out.door = val;

        } else if (type == 0x52) {
            var val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]);
            out.kepcoAlarmMap = val.toString(16);

        } else if (type == 0x54) {
            var s = i + 2;
            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    out.currSubOne = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x02) {
                    out.currSubTwo = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x03) {
                    out.currSubThr = (data[s + j + 2] << 8) + data[s + j + 3];
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }

        } else if (type == 0x55) {
            var s = i + 2;
            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    out.leakCurrSubOne = (data[s + j + 2] << 8) + data[s + j + 3];
                }
                else if ( sub_type == 0x02) {
                    out.leakCurrSubTwo = (data[s + j + 2] << 8) + data[s + j + 3];
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }

        } else if (type == 0x56) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.voltage = val;

        } else if (type == 0x57) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.kepcoPress = val;

        } else if (type == 0x59) {
            var s = i + 2;
            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    out.cntSubTemp = (data[s + j + 2] << 8) + data[s + j + 3];
                } else if ( sub_type == 0x02) {
                    out.cntSubSen1Res = (data[s + j + 2] << 8) + data[s + j + 3];
                } else if ( sub_type == 0x03) {
                    out.cntSubSen2Res = (data[s + j + 2] << 8) + data[s + j + 3];
                } else if ( sub_type == 0x04) {
                    out.cntSubSen1PPM = (data[s + j + 2] << 8) + data[s + j + 3];
                } else if ( sub_type == 0x05) {
                    out.cntSubSen2PPM = (data[s + j + 2] << 8) + data[s + j + 3];
                } else if ( sub_type == 0x06) {
                    out.cntSubSen1Ratio = (data[s + j + 2] << 8) + data[s + j + 3];
                } else if ( sub_type == 0x07) {
                    out.cntSubSen2Ratio = (data[s + j + 2] << 8) + data[s + j + 3];
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }
        } else if (type == 0x5B) {
            var val = data[i + 2];
            switch (length)
            {
                case 4:
                {
                    out.ch1_A = (data[i + 2] << 8) + data[i + 3];
                    out.ch1_B = (data[i + 4] << 8) + data[i + 5];
                    break;
                }
                case 8:
                {
                    out.ch1_A = (data[i + 2] << 8) + data[i + 3];
                    out.ch1_B = (data[i + 4] << 8) + data[i + 5];
                    out.ch2_A = (data[i + 6] << 8) + data[i + 7];
                    out.ch2_B = (data[i + 8] << 8) + data[i + 9];
                    break;
                }
                case 12:
                {
                    out.ch1_A = (data[i + 2] << 8) + data[i + 3];
                    out.ch1_B = (data[i + 4] << 8) + data[i + 5];
                    out.ch2_A = (data[i + 6] << 8) + data[i + 7];
                    out.ch2_B = (data[i + 8] << 8) + data[i + 9];
                    out.ch3_A = (data[i + 10] << 8) + data[i + 11];
                    out.ch3_B = (data[i + 12] << 8) + data[i + 13];
                    break;
                }
                case 16:
                {
                    out.ch1_A = (data[i + 2] << 8) + data[i + 3];
                    out.ch1_B = (data[i + 4] << 8) + data[i + 5];
                    out.ch2_A = (data[i + 6] << 8) + data[i + 7];
                    out.ch2_B = (data[i + 8] << 8) + data[i + 9];
                    out.ch3_A = (data[i + 10] << 8) + data[i + 11];
                    out.ch3_B = (data[i + 12] << 8) + data[i + 13];
                    out.ch4_A = (data[i + 14] << 8) + data[i + 15];
                    out.ch4_B = (data[i + 16] << 8) + data[i + 17];
                    break;
                }
            }

        } else if (type == 0x5C) {
            var val = data[i + 2];
            var s = i + 2;
            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x00)
                {
                    switch(sub_len)
                    {
                        case 4:
                        {
                            out.soil0Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            break;
                        }
                        case 8:
                        {
                            out.soil0Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil0Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            break;
                        }
                        case 12:
                        {
                            out.soil0Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil0Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil0Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            break;
                        }
                        case 16:
                        {
                            out.soil0Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil0Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil0Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            out.soil0Ch4 = (data[s + j + 14] << 24) + (data[s + j + 15] << 16) + (data[s + j + 16] << 8) + data[s + j + 17];
                            break;
                        }
                    }
                }
                else if ( sub_type == 0x01)
                {
                    switch(sub_len)
                    {
                        case 4:
                        {
                            out.soil1Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            break;
                        }
                        case 8:
                        {
                            out.soil1Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil1Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            break;
                        }
                        case 12:
                        {
                            out.soil1Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil1Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil1Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            break;
                        }
                        case 16:
                        {
                            out.soil1Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil1Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil1Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            out.soil1Ch4 = (data[s + j + 14] << 24) + (data[s + j + 15] << 16) + (data[s + j + 16] << 8) + data[s + j + 17];
                            break;
                        }
                    }
                }
                else if ( sub_type == 0x02)
                {
                    switch(sub_len)
                    {
                        case 4:
                        {
                            out.soil2Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            break;
                        }
                        case 8:
                        {
                            out.soil2Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil2Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            break;
                        }
                        case 12:
                        {
                            out.soil2Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil2Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil2Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            break;
                        }
                        case 16:
                        {
                            out.soil2Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil2Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil2Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            out.soil2Ch4 = (data[s + j + 14] << 24) + (data[s + j + 15] << 16) + (data[s + j + 16] << 8) + data[s + j + 17];
                            break;
                        }
                    }

                }
                else if ( sub_type == 0x03)
                {
                    switch(sub_len)
                    {
                        case 4:
                        {
                            out.soil3Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            break;
                        }
                        case 8:
                        {
                            out.soil3Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil3Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            break;
                        }
                        case 12:
                        {
                            out.soil3Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil3Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil3Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            break;
                        }
                        case 16:
                        {
                            out.soil3Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil3Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil3Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            out.soil3Ch4 = (data[s + j + 14] << 24) + (data[s + j + 15] << 16) + (data[s + j + 16] << 8) + data[s + j + 17];
                            break;
                        }
                    }
                }
                else if ( sub_type == 0x04)
                {
                    switch(sub_len)
                    {
                        case 4:
                        {
                            out.soil4Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            break;
                        }
                        case 8:
                        {
                            out.soil4Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil4Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            break;
                        }
                        case 12:
                        {
                            out.soil4Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil4Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil4Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            break;
                        }
                        case 16:
                        {
                            out.soil4Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil4Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil4Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            out.soil4Ch4 = (data[s + j + 14] << 24) + (data[s + j + 15] << 16) + (data[s + j + 16] << 8) + data[s + j + 17];
                            break;
                        }
                    }
                }
                else if ( sub_type == 0x05)
                {
                    switch(sub_len)
                    {
                        case 4:
                        {
                            out.soil5Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            break;
                        }
                        case 8:
                        {
                            out.soil5Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil5Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            break;
                        }
                        case 12:
                        {
                            out.soil5Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil5Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil5Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            break;
                        }
                        case 16:
                        {
                            out.soil5Ch1 = (data[s + j + 2] << 24) + (data[s + j + 3] << 16) + (data[s + j + 4] << 8) + data[s + j + 5];
                            out.soil5Ch2 = (data[s + j + 6] << 24) + (data[s + j + 7] << 16) + (data[s + j + 8] << 8) + data[s + j + 9];
                            out.soil5Ch3 = (data[s + j + 10] << 24) + (data[s + j + 11] << 16) + (data[s + j + 12] << 8) + data[s + j + 13];
                            out.soil5Ch4 = (data[s + j + 14] << 24) + (data[s + j + 15] << 16) + (data[s + j + 16] << 8) + data[s + j + 17];
                            break;
                        }
                    }

                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }


        } else if (type == 0x5D) {
            var val = data[i + 2];
            switch (length)
            {
                case 9:
                {
                    out.gpsLock =  data[i + 2];
                    out.gpsLat = (((data[i + 3] << 24) + (data[i + 4] << 16) + (data[i + 5] << 8) + (data[i + 6]))/100000).toString();
                    out.gpsLon = (((data[i + 7] << 24) + (data[i + 8] << 16) + (data[i + 9] << 8) + (data[i + 10]))/100000).toString();
                    break;
                }
            }

        } else if (type == 0x5E) {
            var val = data[i + 2];
            switch (length)
            {
                case 2:
                {
                    out.step1 = (data[i + 2] << 8) + data[i + 3];
                    break;
                }
                case 4:
                {
                    out.step1 = (data[i + 2] << 8) + data[i + 3];
                    out.step2 = (data[i + 4] << 8) + data[i + 5];
                    break;
                }
                case 6:
                {
                    out.step1 = (data[i + 2] << 8) + data[i + 3];
                    out.step2 = (data[i + 4] << 8) + data[i + 5];
                    out.step3 = (data[i + 6] << 8) + data[i + 7];
                    break;
                }
            }

        } else if (type == 0x5F) {
            var val = data[i + 2];
            switch (length)
            {
                case 5:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    break;
                }
                case 10:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }

                    out.beacon2Major = (data[i + 7] << 8) + data[i + 8];
                    out.beacon2Minor = (data[i + 9] << 8) + data[i + 10];
                    var sign = data[i + 11] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 11]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 11].toString();
                    }
                    break;
                }
                case 15:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }

                    out.beacon2Major = (data[i + 7] << 8) + data[i + 8];
                    out.beacon2Minor = (data[i + 9] << 8) + data[i + 10];
                    var sign = data[i + 11] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 11]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 11].toString();
                    }

                    out.beacon3Major = (data[i + 12] << 8) + data[i + 13];
                    out.beacon3Minor = (data[i + 14] << 8) + data[i + 15];
                    var sign = data[i + 16] & (1 << 7);
                    if(sign)
                    {
                        out.beacon3Rssi = (0xFFFFFF00 | data[i + 16]).toString();
                    }
                    else
                    {
                        out.beacon3Rssi = data[i + 16].toString();
                    }
                    break;
                }
            }
        } else if (type == 0x60) {
            var val = data[i + 2];
            switch (length)
            {
                case 6:
                {
                    out.TeloSf1SubA = (data[i + 2] << 8) + data[i + 3];
                    out.TeloSf1SubB = (data[i + 4] << 8) + data[i + 5];
                    out.TeloSf1DAC = (data[i + 6] << 8) + data[i + 7];
                    break;
                }
                case 12:
                {
                    out.TeloSf1SubA = (data[i + 2] << 8) + data[i + 3];
                    out.TeloSf1SubB = (data[i + 4] << 8) + data[i + 5];
                    out.TeloSf1DAC = (data[i + 6] << 8) + data[i + 7];
                    out.TeloSf2SubA = (data[i + 8] << 8) + data[i + 9];
                    out.TeloSf2SubB = (data[i + 10] << 8) + data[i + 11];
                    out.TeloSf2DAC = (data[i + 12] << 8) + data[i + 13];
                    break;
                }
                case 18:
                {
                    out.TeloSf1SubA = (data[i + 2] << 8) + data[i + 3];
                    out.TeloSf1SubB = (data[i + 4] << 8) + data[i + 5];
                    out.TeloSf1DAC = (data[i + 6] << 8) + data[i + 7];
                    out.TeloSf2SubA = (data[i + 8] << 8) + data[i + 9];
                    out.TeloSf2SubB = (data[i + 10] << 8) + data[i + 11];
                    out.TeloSf2DAC = (data[i + 12] << 8) + data[i + 13];
                    out.TeloSf3SubA = (data[i + 14] << 8) + data[i + 15];
                    out.TeloSf3SubB = (data[i + 16] << 8) + data[i + 17];
                    out.TeloSf3DAC = (data[i + 18] << 8) + data[i + 19];
                    break;
                }
                case 24:
                {
                    out.TeloSf1SubA = (data[i + 2] << 8) + data[i + 3];
                    out.TeloSf1SubB = (data[i + 4] << 8) + data[i + 5];
                    out.TeloSf1DAC = (data[i + 6] << 8) + data[i + 7];
                    out.TeloSf2SubA = (data[i + 8] << 8) + data[i + 9];
                    out.TeloSf2SubB = (data[i + 10] << 8) + data[i + 11];
                    out.TeloSf2DAC = (data[i + 12] << 8) + data[i + 13];
                    out.TeloSf3SubA = (data[i + 14] << 8) + data[i + 15];
                    out.TeloSf3SubB = (data[i + 16] << 8) + data[i + 17];
                    out.TeloSf3DAC = (data[i + 18] << 8) + data[i + 19];
                    out.TeloSf4SubA = (data[i + 20] << 8) + data[i + 21];
                    out.TeloSf4SubB = (data[i + 22] << 8) + data[i + 23];
                    out.TeloSf4DAC = (data[i + 24] << 8) + data[i + 25];
                    break;
                }
            }

        } else if (type == 0x61) {
            var val = data[i + 2];
            switch (length)
            {
                case 3:
                {
                    /* out.temperature = (val/10).toString(); */
                    var sign = val  & (1 << 7);
                    if(sign)
                    {
                        out.X_angle = (0xFFFFFF00 | val).toString();
                    }
                    else
                    {
                        out.X_angle = val.toString();
                    }

                    val = data[i + 3];
                    sign = val  & (1 << 7);
                    if(sign)
                    {
                        out.Y_angle = (0xFFFFFF00 | val).toString();
                    }
                    else
                    {
                        out.Y_angle = val.toString();
                    }

                    val = data[i + 4];
                    sign = val & (1 << 7);
                    if(sign)
                    {
                        out.Z_angle = (0xFFFFFF00 | val).toString();
                    }
                    else
                    {
                        out.Z_angle = val.toString();
                    }

                    break;
                }
            }

        } else if (type == 0x62) {
            var val = data[i + 2];
            switch (length)
            {
                case 6:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Count = data[i + 7];
                    break;
                }
                case 12:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Count = data[i + 7];

                    out.beacon2Major = (data[i + 8] << 8) + data[i + 9];
                    out.beacon2Minor = (data[i + 10] << 8) + data[i + 11];
                    var sign = data[i + 12] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 12]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 12].toString();
                    }
                    out.beacon2Count = data[i + 13];
                    break;
                }
                case 18:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Count = data[i + 7];

                    out.beacon2Major = (data[i + 8] << 8) + data[i + 9];
                    out.beacon2Minor = (data[i + 10] << 8) + data[i + 11];
                    var sign = data[i + 12] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 12]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 12].toString();
                    }
                    out.beacon2Count = data[i + 13];

                    out.beacon3Major = (data[i + 14] << 8) + data[i + 15];
                    out.beacon3Minor = (data[i + 16] << 8) + data[i + 17];
                    var sign = data[i + 18] & (1 << 7);
                    if(sign)
                    {
                        out.beacon3Rssi = (0xFFFFFF00 | data[i + 18]).toString();
                    }
                    else
                    {
                        out.beacon3Rssi = data[i + 18].toString();
                    }
                    out.beacon3Count = data[i + 19];
                    break;
                }
            }
        } else if (type == 0x63) {
            var sign = data[i + 2] & (1 << 7);
            if(sign)
            {
                out.x_axis = (0xFFFF0000 | ((data[i + 2] << 8) + data[i + 3])).toString();
            }
            else
            {
                out.x_axis = ((data[i + 2] << 8) + data[i + 3]).toString();
            }
            sign = data[i + 4] & (1 << 7);
            if(sign)
            {
                out.y_axis = (0xFFFF0000 | ((data[i + 4] << 8) + data[i + 5])).toString();
            }
            else
            {
                out.y_axis = ((data[i + 4] << 8) + data[i + 5]).toString();
            }
            sign = data[i + 6] & (1 << 7);
            if(sign)
            {
                out.z_axis = (0xFFFF0000 | ((data[i + 6] << 8) + data[i + 7])).toString();
            }
            else
            {
                out.z_axis = ((data[i + 6] << 8) + data[i + 7]).toString();
            }
        } else if (type == 0x64) {
            var val = data[i + 2];
            switch (length)
            {
                case 12:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Count = data[i + 7];
                    var mac = new Array(data[i + 8], data[i + 9], data[i + 10], data[i + 11],
                                        data[i + 12], data[i + 13]);
                    out.beacon1Mac = toHexString(mac);
                    break;
                }
                case 24:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Count = data[i + 7];
                    var mac = new Array(data[i + 8], data[i + 9], data[i + 10], data[i + 11],
                                        data[i + 12], data[i + 13]);
                    out.beacon1Mac = toHexString(mac);

                    out.beacon2Major = (data[i + 14] << 8) + data[i + 15];
                    out.beacon2Minor = (data[i + 16] << 8) + data[i + 17];
                    var sign = data[i + 18] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 18]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 18].toString();
                    }
                    out.beacon2Count = data[i + 19];
                    var mac = new Array(data[i + 20], data[i + 21], data[i + 22], data[i + 23],
                                        data[i + 24], data[i + 25]);
                    out.beacon2Mac = toHexString(mac);

                    break;
                }
                case 36:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Count = data[i + 7];
                    var mac = new Array(data[i + 8], data[i + 9], data[i + 10], data[i + 11],
                                        data[i + 12], data[i + 13]);
                    out.beacon1Mac = toHexString(mac);

                    out.beacon2Major = (data[i + 14] << 8) + data[i + 15];
                    out.beacon2Minor = (data[i + 16] << 8) + data[i + 17];
                    var sign = data[i + 18] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 18]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 18].toString();
                    }
                    out.beacon2Count = data[i + 19];
                    var mac = new Array(data[i + 20], data[i + 21], data[i + 22], data[i + 23],
                                        data[i + 24], data[i + 25]);
                    out.beacon2Mac = toHexString(mac);

                    out.beacon3Major = (data[i + 26] << 8) + data[i + 27];
                    out.beacon3Minor = (data[i + 28] << 8) + data[i + 29];
                    var sign = data[i + 30] & (1 << 7);
                    if(sign)
                    {
                        out.beacon3Rssi = (0xFFFFFF00 | data[i + 30]).toString();
                    }
                    else
                    {
                        out.beacon3Rssi = data[i + 30].toString();
                    }
                    out.beacon3Count = data[i + 31];
                    var mac = new Array(data[i + 32], data[i + 33], data[i + 34], data[i + 35],
                                        data[i + 36], data[i + 37]);
                    out.beacon3Mac = toHexString(mac);
                    break;
                }
            }
        } else if (type == 0x65) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.loadcell = (val/10).toString();
        } else if (type == 0x66) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }
            out.crackmeter = (val/10).toString();
        } else if (type == 0x67) {
            var val = data[i + 2];
            switch (length)
            {
                case 6:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }
                    out.beacon1Batt = data[i + 7];
                    break;
                }
                case 12:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }

                    out.beacon1Batt = data[i + 7];

                    out.beacon2Major = (data[i + 8] << 8) + data[i + 9];
                    out.beacon2Minor = (data[i + 10] << 8) + data[i + 11];
                    var sign = data[i + 12] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 12]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 12].toString();
                    }
                    out.beacon2Batt = data[i + 13];
                    break;
                }
                case 18:
                {
                    out.beacon1Major = (data[i + 2] << 8) + data[i + 3];
                    out.beacon1Minor = (data[i + 4] << 8) + data[i + 5];
                    var sign = data[i + 6] & (1 << 7);
                    if(sign)
                    {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 6]).toString();
                    }
                    else
                    {
                        out.beacon1Rssi = data[i + 6].toString();
                    }

                    out.beacon1Batt = data[i + 7];

                    out.beacon2Major = (data[i + 8] << 8) + data[i + 9];
                    out.beacon2Minor = (data[i + 10] << 8) + data[i + 11];
                    var sign = data[i + 12] & (1 << 7);
                    if(sign)
                    {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 12]).toString();
                    }
                    else
                    {
                        out.beacon2Rssi = data[i + 12].toString();
                    }
                    out.beacon2Batt = data[i + 13];

                    out.beacon3Major = (data[i + 14] << 8) + data[i + 15];
                    out.beacon3Minor = (data[i + 16] << 8) + data[i + 17];
                    var sign = data[i + 18] & (1 << 7);
                    if(sign)
                    {
                        out.beacon3Rssi = (0xFFFFFF00 | data[i + 18]).toString();
                    }
                    else
                    {
                        out.beacon3Rssi = data[i + 18].toString();
                    }

                    out.beacon3Batt = data[i + 19];
                    break;
                }
            }
        } else if (type == 0x68) {
            var val = data[i + 2];
            switch (length)
            {
                case 6:
                {
                    /* out.temperature = (val/10).toString(); */
                    /* x angle */
                    val = (data[i + 2] << 8) + data[i + 3];
                    var sign = val & (1 << 15);
                    if(sign)
                    {
                        out.X_angle = ((0xFFFF0000 | val)/100).toString();
                    }
                    else
                    {
                        out.X_angle = (val/100).toString();
                    }

                    /* y angle */
                    val = (data[i + 4] << 8) + data[i + 5];
                    sign = val & (1 << 15);
                    if(sign)
                    {
                        out.Y_angle = ((0xFFFF0000 | val)/100).toString();
                    }
                    else
                    {
                        out.Y_angle = (val/100).toString();
                    }

                    /* z angle */
                    val = (data[i + 6] << 8) + data[i + 7];
                    sign = val & (1 << 15);
                    if(sign)
                    {
                        out.Z_angle = ((0xFFFF0000 | val)/100).toString();
                    }
                    else
                    {
                        out.Z_angle = (val/100).toString();
                    }

                    break;
                }
            }
        } else if (type == 0x69) {
            var val = data[i + 2];
            switch (length)
            {
                case 30:
                {
                    out.beacon10Minor = (data[i + 29] << 8) + data[i + 30];
                    var sign = data[i + 31] & (1 << 7);
                    if(sign) {
                        out.beacon10Rssi = (0xFFFFFF00 | data[i + 31]).toString();
                    } else {
                        out.beacon10Rssi = data[i + 31].toString();
                    }
                }
                case 27:
                {
                    out.beacon9Minor = (data[i + 26] << 8) + data[i + 27];
                    var sign = data[i + 28] & (1 << 7);
                    if(sign) {
                        out.beacon9Rssi = (0xFFFFFF00 | data[i + 28]).toString();
                    } else {
                        out.beacon9Rssi = data[i + 28].toString();
                    }
                }
                case 24:
                {
                    out.beacon8Minor = (data[i + 23] << 8) + data[i + 24];
                    var sign = data[i + 25] & (1 << 7);
                    if(sign) {
                        out.beacon8Rssi = (0xFFFFFF00 | data[i + 25]).toString();
                    } else {
                        out.beacon8Rssi = data[i + 25].toString();
                    }
                }
                case 21:
                {
                    out.beacon7Minor = (data[i + 20] << 8) + data[i + 21];
                    var sign = data[i + 22] & (1 << 7);
                    if(sign) {
                        out.beacon7Rssi = (0xFFFFFF00 | data[i + 22]).toString();
                    } else {
                        out.beacon7Rssi = data[i + 22].toString();
                    }
                }
                case 18:
                {
                    out.beacon6Minor = (data[i + 17] << 8) + data[i + 18];
                    var sign = data[i + 19] & (1 << 7);
                    if(sign) {
                        out.beacon6Rssi = (0xFFFFFF00 | data[i + 19]).toString();
                    } else {
                        out.beacon6Rssi = data[i + 19].toString();
                    }
                }
                case 15:
                {
                    out.beacon5Minor = (data[i + 14] << 8) + data[i + 15];
                    var sign = data[i + 16] & (1 << 7);
                    if(sign) {
                        out.beacon5Rssi = (0xFFFFFF00 | data[i + 16]).toString();
                    } else {
                        out.beacon5Rssi = data[i + 16].toString();
                    }
                }
                case 12:
                {
                    out.beacon4Minor = (data[i + 11] << 8) + data[i + 12];
                    var sign = data[i + 13] & (1 << 7);
                    if(sign) {
                        out.beacon4Rssi = (0xFFFFFF00 | data[i + 13]).toString();
                    } else {
                        out.beacon4Rssi = data[i + 13].toString();
                    }
                }
                case 9:
                {
                    out.beacon3Minor = (data[i + 8] << 8) + data[i + 9];
                    var sign = data[i + 10] & (1 << 7);
                    if(sign) {
                        out.beacon3Rssi = (0xFFFFFF00 | data[i + 10]).toString();
                    } else {
                        out.beacon3Rssi = data[i + 10].toString();
                    }
                }
                case 6:
                {
                    out.beacon2Minor = (data[i + 5] << 8) + data[i + 6];
                    var sign = data[i + 7] & (1 << 7);
                    if(sign) {
                        out.beacon2Rssi = (0xFFFFFF00 | data[i + 7]).toString();
                    } else {
                        out.beacon2Rssi = data[i + 7].toString();
                    }
                }
                case 3:
                {

                    out.beacon1Minor = (data[i + 2] << 8) + data[i + 3];
                    var sign = data[i + 4] & (1 << 7);
                    if(sign) {
                        out.beacon1Rssi = (0xFFFFFF00 | data[i + 4]).toString();
                    } else {
                        out.beacon1Rssi = data[i + 4].toString();
                    }
                    break;
                }
            }
        } else if (type == 0x6B) {
            var val = data[i + 2];
            switch (length)
            {
                case 35:
                {
                    var mac = new Array(data[i + 30], data[i + 31], data[i + 32], data[i + 33],
                                        data[i + 34], data[i + 35]);
                    out.beacon5Mac = toHexString(mac);
                    out.beacon5Count = data[i + 36];
                }
                case 28:
                {
                    var mac = new Array(data[i + 23], data[i + 24], data[i + 25], data[i + 26],
                                        data[i + 27], data[i + 28]);
                    out.beacon4Mac = toHexString(mac);
                    out.beacon4Count = data[i + 29];
                }
                case 21:
                {
                    var mac = new Array(data[i + 16], data[i + 17], data[i + 18], data[i + 19],
                                        data[i + 20], data[i + 21]);
                    out.beacon3Mac = toHexString(mac);
                    out.beacon3Count = data[i + 22];
                }
                case 14:
                {
                    var mac = new Array(data[i + 9], data[i + 10], data[i + 11], data[i + 12],
                                        data[i + 13], data[i + 14]);
                    out.beacon2Mac = toHexString(mac);
                    out.beacon2Count = data[i + 15];
                }
                case 7:
                {
                    var mac = new Array(data[i + 2], data[i + 3], data[i + 4], data[i + 5],
                                        data[i + 6], data[i + 7]);
                    out.beacon1Mac = toHexString(mac);
                    out.beacon1Count = data[i + 8];
                }
                break;
            }
        } else if (type == 0x6C) {
            var val = data[i + 2];
            switch (length)
            {
                case 36:
                {
                    var mac = new Array(data[i + 32], data[i + 33], data[i + 34], data[i + 35],
                                        data[i + 36], data[i + 37]);
                    out.beacon6Mac = toHexString(mac);
                }
                case 30:
                {
                    var mac = new Array(data[i + 26], data[i + 27], data[i + 28], data[i + 29],
                                        data[i + 30], data[i + 31]);
                    out.beacon5Mac = toHexString(mac);
                }
                case 24:
                {
                    var mac = new Array(data[i + 20], data[i + 21], data[i + 22], data[i + 23],
                                        data[i + 24], data[i + 25]);
                    out.beacon4Mac = toHexString(mac);
                }
                case 18:
                {
                    var mac = new Array(data[i + 14], data[i + 15], data[i + 16], data[i + 17],
                                        data[i + 18], data[i + 19]);
                    out.beacon3Mac = toHexString(mac);
                }
                case 12:
                {
                    var mac = new Array(data[i + 8], data[i + 9], data[i + 10], data[i + 11],
                                        data[i + 12], data[i + 13]);
                    out.beacon2Mac = toHexString(mac);
                }
                case 6:
                {
                    var mac = new Array(data[i + 2], data[i + 3], data[i + 4], data[i + 5],
                                        data[i + 6], data[i + 7]);
                    out.beacon1Mac = toHexString(mac);
                }
                break;
            }
        } else if (type == 0x6D) {
            var val = data[i + 2];
            switch (length)
            {
                case 18:
                out.ductID = data.toString('ascii', (i + 2), (i + 2 + 13));
                out.ductBatt = data[i + 2 + 13];
                val = (data[i + 2 + 14] << 24) + (data[i + 2 + 15] << 16) + (data[i + 2 + 16] << 8) + (data[i + 2 + 17]);
                out.ductWeight = (val/10).toString();
                break;
            }
        } else if (type == 0x6E) {
            var val = data[i + 2];
            switch (length)
            {
                case 4:
                out.steamTemp1 = (data[i + 2] << 8) + data[i + 3];
                out.steamTemp2 = (data[i + 4] << 8) + data[i + 5];
                break;
            }
        } else if (type == 0x6F) {
            var val = data[i + 2];
            switch (length)
            {
                case 1:
                out.greenO2 = data[i + 2];
                break;
            }
        } else if (type == 0xA1) {
            var val = data[i + 2];
            switch (length)
            {
                case 8:
                out.hoistDoor1 = data[i + 2];
                out.hoistDoor2 = data[i + 3];
                var mac = new Array(data[i + 4], data[i + 5], data[i + 6], data[i + 7],
                                    data[i + 8], data[i + 9]);
                out.hoistBconMac = toHexString(mac);
                break;
            }
        } else if (type == 0x78) {
            out.kepcoEL = data.toString('ascii', (i + 2), (i + 2 + length));

        } else if (type == 0x80) {
            out.alwaysOn = data[i + 2];

        } else if (type == 0xA2) {
            out.sesSerial = data.toString('ascii', (i + 2), (i + 2 + 12));
            out.sesStatus = data[i + 2 + 12].toString(16);
            out.sesNotUse = (data[i + 2 + 12] >> 7) & 0x1;
            out.sesEmptyPipe = (data[i + 2 + 12] >> 6) & 0x1;
            out.sesReverseFlow = (data[i + 2 + 12] >> 5) & 0x1;
            out.sesLeakage = (data[i + 2 + 12] >> 4) & 0x1;
            out.sesBattLevel = (data[i + 2 + 12]) & 0x0F;
            out.sesValue = ((data[i + 2 + 13] << 24) + (data[i + 2 + 14] << 16) + (data[i + 2 + 15] << 8) + (data[i + 2 + 16]))/1000 ;

        } else if (type == 0xA3) {

            var n = length/9;
            var result = "";
            //var obj = new Object();
            var co = 0;
            var arry = [];
            let n_str;
            let uuid ="";

            for(var co = 0; co < n; co++) {
                arry[co] = new Object();

                arry[co].mac = "00:00:00:00:00:00";
                arry[co].majorVer = (data[i + 2 + 9*co] << 8) + data[i + 3 + 9*co];
                arry[co].minorVer = (data[i + 4 + 9*co] << 8) + data[i + 5 + 9*co];
                arry[co].UUID = "53616D73-756E-6720-456C-65632043";

                let uuid ="";
                for(let kk = 6; kk < 8; kk++)
                {
                    n_str = data[i + kk + 9*co].toString(16).toUpperCase();
                    if(n_str.length < 2)
                        n_str = '0' + n_str;
                    uuid += n_str;
                }
                arry[co].UUID += uuid;

                let sign = data[i + 8 + 9*co] & (1 << 7);
                if(sign)
                {
                    arry[co].txPower = (0xFFFFFF00 | data[i + 8 + 9*co]);
                }
                else
                {
                    arry[co].txPower = data[i + 8 + 9*co];
                }

                sign = data[i + 9 + 9*co] & (1 << 7);
                if(sign)
                {
                    arry[co].rssi = (0xFFFFFF00 | data[i + 9 + 9*co]);
                }
                else
                {
                    arry[co].rssi = data[i + 9 + 9*co];
                }
                arry[co].sos = (data[i + 10 + 9*co] >> 7) & 0x1;
                arry[co].move = (data[i + 10 + 9*co] >> 4) & 0x7;
                arry[co].battLevel = ((data[i + 10 + 9*co] >> 0) & 0x0F) * 10;
            }

            out.data_length = n;
            out.data = arry;

        } else if (type == 0xA4) {

            /* Firmware version */
            if(length == 2)
            {
                let major = data[i + 2].toString();
                let minor = data[i + 3].toString();
                if(minor.length < 2)
                    minor = '0' + minor;
                out.fwVer = major + '.' + minor;
            }
        } else if (type == 0xA5) {

            if(length == 36)
            {
                out.solarVoltage = ((data[i + 2] << 8) + (data[i + 2 + 1]))/100;
                out.solarCurrent = ((data[i + 2 + 2] << 8) + (data[i + 2 + 3]))/100;
                out.solarPower = ((data[i + 2 + 4] << 8) + (data[i + 2 + 5]) + (data[i + 2 + 6] << 24) + (data[i + 2 + 7] << 16))/100;

                out.battVoltage = ((data[i + 2 + 8] << 8) + (data[i + 2 + 9]))/100;
                out.battCurrent = ((data[i + 2 + 10] << 8) + (data[i + 2 + 11]))/100;
                out.battPower = ((data[i + 2 + 12] << 8) + (data[i + 2 + 13]) + (data[i + 2 + 14] << 24) + (data[i + 2 + 15] << 16))/100;

                out.loadVoltage = ((data[i + 2 + 16] << 8) + (data[i + 2 + 17]))/100;
                out.loadCurrent = ((data[i + 2 + 18] << 8) + (data[i + 2 + 19]))/100;
                out.loadPower = ((data[i + 2 + 20] << 8) + (data[i + 2 + 21]) + (data[i + 2 + 22] << 24) + (data[i + 2 + 23] << 16))/100;

                let val = (data[i + 2 + 24] << 8) + (data[i + 2 + 25]);
                let sign = val & (1 << 15);
                if(sign)
                {
                    out.battTemp = ((0xFFFF0000 | val)/100);
                }
                else
                {
                    out.battTemp = (val/100);
                }

                val = (data[i + 2 + 26] << 8) + (data[i + 2 + 27]);
                sign = val & (1 << 15);
                if(sign)
                {
                    out.devTemp = ((0xFFFF0000 | val)/100);
                }
                else
                {
                    out.devTemp = (val/100);
                }

                out.battSOC = (data[i + 2 + 30] << 8) + (data[i + 2 + 31]) + 13;

                let battStatus = ((data[i + 2 + 32] << 8) + (data[i + 2 + 33]) & 0x000F);
                if(battStatus == 0)
                    out.battStatus = "Normal";
                else if (battStatus == 1)
                    out.battStatus = "OverVoltage";
                else if (battStatus == 2)
                    out.battStatus = "UnderVoltage";
                else if (battStatus == 3)
                    out.battStatus = "Low Volt Disconnect";
                else if (battStatus == 4)
                    out.battStatus = "Fault";
                else
                    out.battStatus = "Unknown";

                let ChargingStatus = (((data[i + 2 + 34] << 8) + (data[i + 2 + 35])) >> 2) & 0x3;
                if(ChargingStatus == 0)
                    out.chargingStatus = "No Charging";
                else if(ChargingStatus == 1)
                    out.chargingStatus = "Float";
                else if(ChargingStatus == 2)
                    out.chargingStatus = "Boost";
                else if(ChargingStatus == 3)
                    out.chargingStatus = "Equlization";
            }
        } else if (type == 0xC0) {
            var val = data[i + 2];
            switch (length)
            {
                case 35:
                {
                    var mac = new Array(data[i + 30], data[i + 31], data[i + 32], data[i + 33],
                                        data[i + 34], data[i + 35]);
                    out.beacon5Mac = toHexString(mac);
                    out.beacon5Batt = data[i + 36];
                }
                case 28:
                {
                    var mac = new Array(data[i + 23], data[i + 24], data[i + 25], data[i + 26],
                                        data[i + 27], data[i + 28]);
                    out.beacon4Mac = toHexString(mac);
                    out.beacon4Batt = data[i + 29];
                }
                case 21:
                {
                    var mac = new Array(data[i + 16], data[i + 17], data[i + 18], data[i + 19],
                                        data[i + 20], data[i + 21]);
                    out.beacon3Mac = toHexString(mac);
                    out.beacon3Batt = data[i + 22];
                }
                case 14:
                {
                    var mac = new Array(data[i + 9], data[i + 10], data[i + 11], data[i + 12],
                                        data[i + 13], data[i + 14]);
                    out.beacon2Mac = toHexString(mac);
                    out.beacon2Batt = data[i + 15];
                }
                case 7:
                {
                    var mac = new Array(data[i + 2], data[i + 3], data[i + 4], data[i + 5],
                                        data[i + 6], data[i + 7]);
                    out.beacon1Mac = toHexString(mac);
                    out.beacon1Batt = data[i + 8];
                }
                break;
            }

        } else if (type == 0xC1) {
            var val = data[i + 2];
            switch (length)
            {
                case 1: val = data[i + 2]; break;
                case 2: val = (data[i + 2] << 8) + data[i + 3]; break;
                case 4: val = (data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + (data[i + 5]); break;
            }

            out.pulse = val;

        } else if (type == 0xC2) {
            var val = data[i + 2];
            switch (length)
            {
                case 4:
                {
                    out.beacon4Batt = data[i + 5];
                }
                case 3:
                {
                    out.beacon3Batt = data[i + 4];
                }
                case 2:
                {
                    out.beacon2Batt = data[i + 3];
                }
                case 1:
                {
                    out.beacon1Batt = data[i + 2];
                }
            }

        } else if (type == 0xC3) {
            var val = data[i + 2];
            switch (length)
            {
                case 15:
                out.RFID = data.toString('ascii', (i + 2), (i + 2 + length));
            }
        } else if (type == 0xC4) {

            let gas_data = new Object();
            let sensing = new Object();
            let info = new Object();
            var s = i + 2;

            for (var j = 0; j < length; ) {

                var sub_type = data[s + j];
                var sub_len = data[s + j + 1];

                if ( sub_type == 0x01) {
                    sensing.LEL = ((data[s + j + 2] << 8) + data[s + j + 3])/100;
                }
                else if ( sub_type == 0x02) {
                    sensing.CO = ((data[s + j + 2] << 8) + data[s + j + 3])/100;
                }
                else if ( sub_type == 0x03) {
                    sensing.H2S = ((data[s + j + 2] << 8) + data[s + j + 3])/100;
                }
                else if ( sub_type == 0x04) {
                    sensing.O2 = ((data[s + j + 2] << 8) + data[s + j + 3])/100;
                }
                else if ( sub_type == 0x05) {
                    sensing.CO2 = ((data[s + j + 2] << 8) + data[s + j + 3])/100;
                }
                else if ( sub_type == 0x06) {
                    info.mandown = data[s + j + 2];
                    info.sos = (data[s + j + 3] >> 7) & 0x1;
                    info.batt = data[s + j + 3] & 0x7F;
                }
                else if ( sub_type == 0x07) {
                    var mac_idx;
                    gas_data.id='';
                    for (var m = 0; m < 6; m++)
                    {
                        mac_idx = (data[s +j + 2 + m] & 0xFF).toString(16);
                        mac_idx = '0' + mac_idx;
                        mac_idx = mac_idx.slice(-2);
                        gas_data.id += mac_idx;
                        if(m < 5)
                            gas_data.id += ':';
                    }
                } else {
                    out.sub_errors += i + ' ';
                    out.sub_errors_type = sub_type;
                    out.sub_errors_len = sub_len;
                }

                j += 1 + 1 + sub_len;
            }

            gas_data.sensing = sensing;
            gas_data.info = info;
            out.gas_data = gas_data;

        } else if (type == 0xC5) {

            let gasTag = new Object();
            let sensing = new Object();
            let info = new Object();
            let mac = new Array( 0x00, 0x13, 0x43, data[i + 2], data[i + 3], data[i + 4]);
            gasTag.id = mac.readBigUInt64BE(0).toString(16).padStart(12, '0');
            
            sensing.LEL = ((data[i + 5] << 8) + data[i + 6])/100;
            sensing.CO = ((data[i + 7] << 8) + data[i + 8])/100;
            sensing.H2S = ((data[i + 9] << 8) + data[i + 10])/100;
            sensing.O2 = ((data[i + 11] << 8) + data[i + 12])/100;
            sensing.CO2 = ((data[i + 13] << 8) + data[i + 14])/100;
            sensing.battery = data[i + 16] & 0x7F;

            info.mandown = data[i + 15];
            info.sos = (data[i + 16] >> 7) & 0x1;

            gasTag.sensing = sensing;
            gasTag.info = info;
            out.gasTag = gasTag;

        } else if (type == 0xC6) {

            let smartBand = new Object();
            let sensing = new Object();
            let mac = new Array( 0x04, 0x32, 0xf4, data[i + 2], data[i + 3], data[i + 4]);
            smartBand.id = mac.readBigUInt64BE(0).toString(16).padStart(12, '0');

            sensing.heartbeat = data[i + 5];
            sensing.step = (data[i + 6] << 8) + data[i + 7];
            sensing.calories = (data[i + 8] << 8) + data[i + 9];
            sensing.distance = (data[i + 10] << 8) + data[i + 11];
            sensing.sleep = data[i + 12];
            sensing.battery = data[i + 13];

            smartBand.sensing = sensing;
            out.smartBand = smartBand;

        } else if (type == 0xC7) {

            let smartBand = new Object();
            let sensing = new Object();
            let mac = new Array( 0x10, 0x20, 0x30, data[i + 2], data[i + 3], data[i + 4]);
            smartBand.id = mac.readBigUInt64BE(0).toString(16).padStart(12, '0');

            sensing.heartbeat = data[i + 5];
            sensing.step = (data[i + 6] << 8) + data[i + 7];
            sensing.calories = (data[i + 8] << 8) + data[i + 9];
            sensing.distance = (data[i + 10] << 8) + data[i + 11];
            sensing.sleep = data[i + 12];
            sensing.temperature = (data[i + 13] << 8) + data[i + 14];

            smartBand.sensing = sensing;
            out.smartBand = smartBand;

        } else if (type == 0xC9) {
            var val = data[i + 2];
            switch (length)
            {
                case 7:
                {
                    out.beaconMac = data.slice(i + 2, i + 8).readBigUInt64BE(0).toString(16).padStart(12, '0')
                    out.beaconBatt = data[i + 8];
                }
                break;
            }
        } else if (type == 0xCA) {
            var val = data[i + 2];
            
            if (length != 47)
                break;
            
            let EH = new Object();
            
            var year = ((data[i + 2] << 8) + data[i + 3]);
            var mon = ('0' + data[i + 4]).slice(-2);
            var day = ('0' + data[i + 5]).slice(-2);
            var hour = ('0' + data[i + 6]).slice(-2);
            var min = ('0' + data[i + 7]).slice(-2);
            var second = ('0' + data[i + 8]).slice(-2);

            EH.date = year + '-' + mon + '-' + day + ' ' + hour + ':' + min + ':' + second; 
            EH.smallParticleCounts = ((data[i + 9] << 24) + (data[i + 10] << 16) + (data[i + 11] << 8) + data[i + 12]);
            EH.largeParticleCounts = ((data[i + 13] << 24) + (data[i + 14] << 16) + (data[i + 15] << 8) + data[i + 16]);
            EH.smallBioCounts = ((data[i + 17] << 8) + data[i + 18]);
            EH.largeBioCounts = ((data[i + 19] << 8) + data[i + 20]);
            EH.particleSizeFraction = ((data[i + 21] << 8) + data[i + 22]);
            EH.algArmedReady = data[i + 23];
            EH.alarmCounter = ((data[i + 24] << 8) + data[i + 25]);
            EH.systemAlarmState = data.toString('ascii', (i + 26), (i + 27));
            EH.gpsEnabled = data[i + 27];
            EH.gpsValid = data[i + 28];
            
            /* 
               hour = ('0' + data[i + 25]).slice(-2);
               min = ('0' + data[i + 26]).slice(-2);
               second = ('0' + data[i + 27]).slice(-2);
               EH.UTCTime = hour + ':' + min + ':' + second; 
            */
            EH.latitude = ((data[i + 29] << 24) + (data[i + 30] << 16) + (data[i + 31] << 8) + data[i + 32])/1000000;
            EH.longitude = ((data[i + 33] << 24) + (data[i + 34] << 16) + (data[i + 35] << 8) + data[i + 36])/1000000;
            EH.altitude = ((data[i + 37] << 8) + data[i + 38])/10;
            EH.exhaustPressure = ((data[i + 39] << 8) + data[i + 40])/100;

            val = data[i + 41];
            var sign = val & (1 << 8);
            if(sign)
            {
                EH.internalTemperature = (0xFFFF0000 | val);
            }
            else
            {
                EH.internalTemperature = val;
            }
            
            EH.laserCurrent = data[i + 42];
            EH.laserPD = ((data[i + 43] << 8) + data[i + 44]);
            EH.backgroundMonitor = data[i + 45]/100;
            EH.powerSupply = data[i + 46]/10;
            EH.inputVoltage = data[i + 47];
            EH.diagFault = data.toString('ascii', (i + 48), (i + 49));

            out.EH = EH;

        } else if (type == 0xCB) {
            var val = data[i + 2];
            let smartDetector = new Object();
            let sensing = new Object();

            if (length != 9)
                break;

            smartDetector.id = data[i + 2] + (data[i + 3] << 8);

            val = data[i + 4] + (data[i + 5] << 8);
            let sign = val & (1 << 15);

            if(sign)
            {
                sensing.temp = ((0xFFFF0000 | val)/10);
            }
            else
            {
                sensing.temp = (val/10);
            }
            sensing.humidity = data[i + 6] + (data[i + 7] << 8);

            val = data[i + 8] + (data[i + 9] << 8);
            sign = val & (1 << 15);

            if(sign)
            {
                sensing.windchilltemp = ((0xFFFF0000 | val)/10);
            }
            else
            {
                sensing.windchilltemp = (val/10);
            }
            sensing.alarm = data[i + 10];

            smartDetector.sensing = sensing;
            out.smartDetector = smartDetector;

        } else if (type == 0xCC) {
            /* PLS200 */
            if(length != 4)
                break;

            out.Status = data[i + 2];
            out.step = (data[i + 3] << 8) + data[i + 4];
            out.battery = data[i + 5];
        } else if (type == 0xCD) {
            /* PLS200 */
            let scanIndex = 0;
            let subLength = length;

            let index = i + 2;
            while (subLength > 0) {
                let subType = data[index];
                let result = null;
                if (subType == 0x05) {
                    out[`beacon${scanIndex}Mac`] = data.slice(index + 1, index + 7).readBigUInt64BE(0).toString(16).padStart(6, '0');
                    out[`beacon${scanIndex}Batt`] = data[index + 8];
                    
                    subLength -= 7;
                    index += 7;
                } else if (subType >= 0x01 && subType <= 0x04) {
                    index++;
                    subLength--;

                    let keyName = `uwb${scanIndex}`;
                    out[keyName] = {};
                    for (let j = 0; j < subType; j++) {
                        let eui = data.slice(index, index + 2).readUInt16BE(0).toString(16).padStart(4, '0');
                        out[keyName][eui] = {
                            'dist': (data[index + 2] >> 3) + ((data[index + 2] & 0b00000111) * 0.125)
                        };
                        subLength -= 3;
                        index += 3;
                    }
                } else {
                    result = `error: unknown subtype`;
                    index += 1;
                    subLength -= 1;
                }

                scanIndex++;
            }
        } else if (type == 0xCE) {
            /* DL ENC. UWB Anchor information */
            var val = data[i + 2];
            if (length == 2)
            {
                out.Status = val;
                out.battery = data[i + 3];
            }
            else if (length == 3)
            {
                out.Status = val;
                out.battery = data[i + 3];
                
                let sign = data[i + 4] & (1 << 7);
                if(sign)
                {
                    out.floor = 'B' + (0xFF - data[i + 4] + 1);
                }
                else
                {
                    out.floor = 'F' + val;
                }
            }
            else if (length == 9)
            {
                out.Status = val;
                out.battery = data[i + 3];
                
                let sign = data[i + 4] & (1 << 7);
                if(sign)
                {
                    out.floor = 'B' + (0xFF - data[i + 4] + 1);
                }
                else
                {
                    out.floor = 'F' + data[i + 4];
                }
                val = data[i + 5];
                if(val == 0)
                    out.opmode ="Normal";
                else if(val == 1)
                    out.opmode ="Test";
                else if(val == 2)
                    out.opmode ="Configuration";
                else 
                    out.opmode ="Unknown";
                val = data[i + 6];
                if(val == 0)
                    out.anchorType ="Location";
                else if(val == 1)
                    out.anchorType ="LoDanger";
                else if(val == 2)
                    out.anchorType ="Danger";
                else 
                    out.anchorType ="Unknown";
                
                out.probe_period = ((data[i + 7] << 24) + (data[i + 8] << 16) + (data[i + 9] << 8) + data[i + 10]);
            }
        } else if (type == 0xCF) {
            /* SAMSUNG Shotcounter */
            var val = data[i + 2];
            if (length == 4)
            {
                out.shotcounter = ((data[i + 2] << 24) + (data[i + 3] << 16) + (data[i + 4] << 8) + data[i + 5]);
            }
        } else if (type == 0xF0) {
            out.battery = data[i + 2];

        } else if (type == 0xF2) {
            out.voltage = (((data[i + 2] << 8) + data[i + 3])/100).toString();
        } else {
            out.errors += i + ' ';
            out.errors_type = type;
            out.errors_len = length;
        }

        i += 1 + 1 + length;
    }

    /* Please fill the user customized code here. */

    return out;
};

/*
  -> Tip. How to convert a string to a JSON object?
  try {
  jsonObj = JSON.parse("{a:10,b:'xxx'}");
  } catch (e) {
  //exception handling.
  }
*/
