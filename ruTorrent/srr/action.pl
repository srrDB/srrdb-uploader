#!/usr/bin/perl -w

use strict;
use CGI;
use File::Basename;
use IPC::Open3;
use Cwd;
use RTPG;
use WWW::Mechanize;
use config;

my $messages = { errors => {}, infos => {} };

# get parameters
my $q = new CGI();
my $infohash = $q->param('infohash');
my $currentpath = getcwd;
handleMessages({ descr => 'theUILang.errorInfohash', }, 'parameters', 1) unless $infohash && $infohash =~ m![0-9A-F]{40}!;
handleMessages({ descr => 'theUILang.errorNoRtorrentSocket' }, 'config', 1) unless config::RTORRENT_SOCKETPATH;

my $rt = RTPG->new(url => config::RTORRENT_SOCKETPATH);
my ($tinfo, $error) = $rt->torrent_info($infohash);
if ($error) {
    $error =~ s!\n! !g;
    handleMessages({ customDescr => $error, prm => { Infohash => $infohash } }, 'rtorrent', 1);
}
handleMessages({ descr => 'theUILang.errorNotComplete', prm => { Torrentname => $tinfo->{name} } }, 'rtorrent', 1) unless $tinfo->{complete};
(my $filelist, $error) = $rt->file_list($infohash);
if ($error) {
    $error =~ s!\n! !g;
    handleMessages({ customDescr => $error, prm => { Torrentname => $tinfo->{name} } }, 'rtorrent', 1);
}
my $basepath = $tinfo->{directory_base};
## get releasename from foldername rather than from rtorrent as it might differ
my ($releasename) = fileparse($basepath);

if (isValid($filelist)) {
    my ($wtr, $rdr, $err);
    use Symbol 'gensym'; $err = gensym;
    my $pid;
	if (config::PYRESCENE_PATH) {
    	handleMessages({ descr => 'theUILang.errorPyrescenepyNotFound' }, 'config', 1) unless -f config::PYRESCENE_PATH.'/pyrescene.py';
    	handleMessages({ descr => 'theUILang.errorPyrescenepyNotExecutable' }, 'config', 1) unless -x config::PYRESCENE_PATH.'/pyrescene.py';
        $pid = open3($wtr, $rdr, $err, 'python '.config::PYRESCENE."/pyrescene.py -y --best -r $basepath -o $currentpath/tmp");
	} else {
        $pid = open3($wtr, $rdr, $err, "pyrescene.py -y --best -r $basepath -o $currentpath/tmp");
	}
    waitpid( $pid, 0 );
    my $child_exit_status = $? >> 8;
    my $msg = '';
    foreach(<$err>) {
        chomp;
        $msg .= $_." ";
    }
    handleMessages({ customDescr => $msg }, 'rescene', 1) if $child_exit_status;
    if (-f "$currentpath/tmp/$releasename.srr") {
        my $mech = WWW::Mechanize->new;
## validate if login was successfull by parsing the output!
        $mech->post('https://www.srrdb.com/account/login', { username => config::SRRUSERNAME, password => config::SRRPASSWORD }) if config::SRRUSERNAME && config::SRRPASSWORD;
        my $result = $mech->post('https://www.srrdb.com/upload', Content_Type => 'form-data', Content => [ file => [ "$currentpath/tmp/$releasename.srr" ], upload => 'upload' ]);
		my ($output) = $result->decoded_content =~ m!<tr title="(.+)" class="color-\d">!;
        unlink "$currentpath/tmp/$releasename.srr" or handleMessages({ descr => 'theUILang.errorDeleteFile', info => $! }, 'file', 0);
		if ($output) {
			handleMessages({ descr => 'theUILang.success', info => $output }, 'default', 0);
		} else {
			handleMessages({ descr => 'theUILang.errorUpload' }, 'default', 0);
		}
    } else {
		## this should not happen, as any error with pyrescene should be rescognized before!
        handleMessages({ descr => 'theUILang.errorCreateSrr' }, 'pyrescene', 1);
    }
} else {
    handleMessages({ descr => 'theUILang.errorNotValid' }, 'default', 1);
}
returnMsgs();

## check if release contains a sfv file and is not from a known p2p group releasing with sfv
sub isValid {
    for (@$filelist) {
        return 1 if $_->{path} =~ m!\.sfv$!i && $_->{path} !~ m!Z3BR4/!;
    }
    return 0;
}

# add all received errors to global error hash
sub handleMessages {

    my ($msg, $key, $exit) = @_;
    my $msgtype = (($exit) ? 'errors' : 'infos');
    $messages->{$msgtype}->{$key} = () unless $messages->{$msgtype}->{$key};
    $msg->{prm}->{Infohash} = $infohash if $infohash;
    $msg->{prm}->{Name} = $releasename if !(grep $_ eq $key, ('config', 'parameters', 'rtorrent'));
    push(@{$messages->{$msgtype}->{$key}}, $msg);
    returnMsgs() if $exit;
}

# return error and info messages to user
sub returnMsgs {

    ## only print content-type if not called by php script
    print "Content-type: application/json\n\n" unless @ARGV;

    # create JSON result string with error and info messages
    my $result = '{';
## check if last char is ',' before each chop or do we consider we always have one message?
    for my $msgtype (reverse sort keys %$messages) {
        $result .= '"'.$msgtype.'": {';
        for my $msgcat (sort keys %{$messages->{$msgtype}}) {
            $result .= '"'.$msgcat.'": [';
            for my $msg (@{$messages->{$msgtype}->{$msgcat}}) {
                if ($msg->{info}) {
                    $msg->{info} =~ s!"!\\"!g;
                }
                if ($msg->{customDescr}) {
                    $msg->{customDescr} =~ s!"!\\"!g;
                    $result .= '{"customDescr": "'.$msg->{customDescr}.'"'.(($msg->{info}) ? ',"info": "'.$msg->{info}.'"' : '');
                } else {
                    $result .= '{"descr": "'.$msg->{descr}.'"'.(($msg->{info}) ? ',"info": "'.$msg->{info}.'"' : '');
                }
                if ($msg->{prm}) {
                    $result .= ', "prm": {';
                    for my $prmName (sort keys %{$msg->{prm}}) {
                        $result .= '"'.$prmName.'": "'.$msg->{prm}->{$prmName}.'",';
                    }
                    chop($result);
                    $result .= '}';
                }
                $result .= '},';
            }
            chop($result);
            $result .= '],';
        }
        chop($result) if substr($result, -1) eq ',';
        $result .= '},';
    }
    chop($result);
    print $result.'}';
    exit;
}
