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
        $('#viewer-bg').html(msg.data);
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
