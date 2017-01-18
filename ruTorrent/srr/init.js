plugin.loadLang();

plugin.onLangLoaded = function() {
    var plg = thePlugins.get('_task');
    if(!plg.allStuffLoaded) {
        setTimeout(arguments.callee,1000);
    } else {
        theWebUI.request('?action=isNginx',[theWebUI.setWebserverName, theWebUI]);
        plugin.markLoaded();
    }
}

plugin.loadMainCSS();
if (browser.isKonqueror) {
    plugin.loadCSS('konqueror');
}

// keep track of the uploads
theWebUI.uploadInfos = { queue: [], isUploading: 0 };

// upload all srrs in queue
theWebUI.createAndUploadSrrs = function() {
	$.each(this.getHashes('srr').split('&hash=').filter(function(e) { return e.length != 0 }), function(i, e) {
   	    if ($.inArray(e, theWebUI.uploadInfos.queue) == -1) {
       	    theWebUI.uploadInfos.queue.push(e);
       	}
    });
    if (!theWebUI.uploadInfos.interval) {
       	theWebUI.uploadInfos.interval = setInterval(theWebUI.tryCreateAndUploadSrrs, 3000);
    }
}

// check if we are already preparing an upload. if not, start next
theWebUI.tryCreateAndUploadSrrs = function() {
   	if (!theWebUI.uploadInfos.isUploading && theWebUI.uploadInfos.queue.length) {
       	theWebUI.uploadInfos.isUploading = 1;
       	theWebUI.requestWithoutTimeout('?action=createAndUploadSrr&v='+encodeURI(theWebUI.uploadInfos.queue[0]),[theWebUI.srrComplete, theWebUI]);
   	}
}

// change right click menu for torrent selection uploads
if (plugin.canChangeMenu()) {
    plugin.createMenu = theWebUI.createMenu;
    theWebUI.createMenu = function(e, id) {
        plugin.createMenu.call(this,e,id);
        if (plugin.enabled && plugin.allStuffLoaded) {
            var el = theContextMenu.get( theUILang.Properties );
            if (el) {
	            theContextMenu.add( el, [theUILang.createSrrs,  "theWebUI.createAndUploadSrrs()"] );
			}
		}
	}
}

// check if we are using nginx as webserver
theWebUI.setWebserverName = function(d) {
    isNginx = d.isNginx;
}

// ajax success function for srr upload
theWebUI.srrComplete = function(d) {
    $.each(d, function(msgtype, msgcats) {
        $.each(msgcats, function(msgcat, msgs) {
            $.each(msgs, function(i, msg) {
                var out;
                if (msg.descr) {
                    out = eval(msg.descr);
                } else if (msg.customDescr) {
                    out = msg.customDescr;
                } else {
                    out = 'Did not find any message, this should not have happend! Please contact plugin creator!';
                }
                if (msg.info) {
                    out += ': '+msg.info;
                }
                if (msg.prm) {
                    out += ' (Parameter: ';
                    $.each(msg.prm, function(k, v) {
                        out += k+" => "+v+" ,";
                    });
                    out = out.slice(0, -1)+')';
                }
                log(((msgtype == 'errors') ? 'ERROR' : 'MESSAGE') + ' ('+msgcat+'): '+out+'!');
                theWebUI.uploadInfos.queue.splice(0, 1);
                if (!theWebUI.uploadInfos.queue.length) {
                    clearInterval(theWebUI.uploadInfos.interval);
                    theWebUI.uploadInfos.interval = 0;
                }
                theWebUI.uploadInfos.isUploading = 0;
            });
        });
    });
}

// remove plugin
plugin.onRemove = function() {
    plugin.removeSeparatorFromToolbar('create');
    plugin.removeButtonFromToolbar('uploadTorrent');
}

// helper function to see if we are using nginx
rTorrentStub.prototype.isNginx = function() {
    this.contentType = 'text/plain';
    this.mountPoint = 'plugins/srr/isNginx.php';
    this.dataType = 'json';
}

// try to create and upload srrs
rTorrentStub.prototype.createAndUploadSrr = function() {
    this.content = encodeURI('&infohash='+this.vs[0]);
    this.contentType = 'application/x-www-form-urlencoded';
    if (isNginx == 1) {
        this.mountPoint = 'plugins/srr/action.php';
    } else {
        this.mountPoint = 'plugins/srr/action.pl';
    }
    this.dataType = 'json';
}
