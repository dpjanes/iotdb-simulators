request = require('superagent')
fs = require('fs');
path = require('path');

var method = "PUT";
var url = null;
var requestd = {};

process.argv.forEach(function(a, index) {
    if (index == 2) {
        url = a;
    } else if (index > 2) {
        var re = /^([^=]*)=(.*)$/;
        var match = re.exec(a);
        if (match) {
            if (match[2] == "false") {
                match[2] = false;
            } else if (match[2] == "true") {
                match[2] = true;
            } else {
                var i = parseInt(match[2]);
                if (match[2] == ("" + i)) {
                    match[2] = i;
                }
            }

            
            var d = requestd;
            var keys = match[1].split("/");
            for (var ki = 0; ki < keys.length - 1; ki++) {
                var key = keys[ki];
                var nd = d[key];
                if (!nd) {
                    d[key] = nd = {};
                }

                d = nd;
            }
            var key = keys[keys.length - 1];
            var value = match[2];

            d[key] = value;
        }
    }
})

do_put = function(url, requestd) {
    console.log("send", requestd);
    request
        .put(url)
        .set('Accept', 'application/json')
        .set('Content-Type', 'application/json')
        .send(requestd)
        .end(function(result) {
            if (!result.ok) {
                console.log("not ok", "url", url, "result", result.text);
                return
            }

            console.log("receive", JSON.stringify(result.body, null, 2));
        })

}

if (url == null) {
    console.log("URL is required!");
    process.exit(1);
} else if (url.substring(0, 4) == "http") {
    do_put(url, requestd);
} else {
    var parts = url.split("/")
    url = parts[0];

    var fname = path.join(process.env['HOME'], ".iot-served", url);
    fs.readFile(fname, 'utf8', function (err, data) { 
        if (err) {
            console.log(err);
            process.exit(1);
        }

        if (!data) {
            console.log("no data?");
            process.exit(1);
        }

        servedd = JSON.parse(data);
        if (!servedd.url) {
            console.log("no url found");
            process.exit(1);
        }

        parts[0] = servedd.url.replace(/\/*$/, "");
        url = parts.join("/")

        console.log("using url", url);

        do_put(url, requestd);
    });
}
