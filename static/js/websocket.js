init_websocket = function() {
    socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('event_monitor', function (msg) {
        console.log(msg.data);
        let stamp = '';
        if(msg.time != undefined){
            stamp = '<li><span>' + msg.time + '</span>' + msg.data + '</li>'
        } else {
                stamp = '<li>' + msg.data + '</li>'
        }
        $('#event-content').prepend(stamp);
    });

    socket.on('state_info', function (msg) {
        // console.log(msg.data);
        if (debug_annotation_state == 1) {
            $('#viewer-bg').html(
                '<ul class="state-info" style="text-align: right">' +
                '<li>Position</li>' +
                '<li>Quaternion</li>' +
                '<li>Z Angle</li>' +
                '<li>Accelerometer</li>' +
                '<li>Gyroscope</li>' +
                '<li>Head Angle</li>' +
                '<li>Lift Height</li>' +
                '<li>Left Wheel</li>' +
                '<li>Right Wheel</li>' +
                '<li>Proximity Sensor</li>' +
                '</ul>' +

                '<ul class="state-info" style="left: 100px">' + 
                '<li>' + msg.position + '</li>' +
                '<li>' + msg.quaternion + '</li>' +
                '<li>' + msg.angle_z + '</li>' +
                '<li>' + msg.accel + '</li>' +
                '<li>' + msg.gyro + '</li>' +
                '<li>' + msg.head + '</li>' +
                '<li>' + msg.lift + '</li>' +
                '<li>' + msg.l_wheel + '</li>' +
                '<li>' + msg.r_wheel + '</li>' +
                '<li>' + msg.proximity + '</li>' +
                '</ul>'
                );
        } else if (debug_annotation_state == 2) {
            $('#viewer-bg').html('');
        }
    });

    socket.onclose = function(event){
        $('#event-content').prepend('<li>CLIENT: Server disconnected.</li>');
    }

    socket.io.on('connect_error', function (error) {
        // handle server error here
        $('#event-content').prepend('<li>CLIENT: Error reaching server. Connection closed.</li>');
        socket.disconnect();
    });

    return socket
};
