#!/usr/bin/perl

use strict;
use File::Basename;
use WWW::Mechanize;
use Log::Log4perl qw(get_logger);
use RTPG;

## USAGE

## 1. add the following to your .rtorrent.rc and adjust the path to this script:
## system.method.set_key = event.download.finished,00_finish,"execute=screen,-dm,perl,/path/to/this/script.pl,$d.hash=,$d.directory_base=,"

## 2. install the following three CPAN modules: RTPG, WWW::Mechanize and Log::Log4perl
## 2a with root privileges:
## sudo cpan App::cpanminus
## sudo cpanm RTPG WWW::Mechanize Log::Log4perl
## 2b without root privileges:
## wget -O- http://cpanmin.us | perl - -l ~/perl5 App::cpanminus local::lib
## eval `perl -I ~/perl5/lib/perl5 -Mlocal::lib`
## echo 'eval `perl -I ~/perl5/lib/perl5 -Mlocal::lib`' >> ~/.profile
## echo 'export MANPATH=$HOME/perl5/man:$MANPATH' >> ~/.profile
## cpanm RTPG WWW::Mechanize Log::Log4perl
## 2c check out http://www.cpan.org/modules/INSTALL.html to see what other options exist

## 3. check and adjust the following constants

use constant {
	## scgi_local or scgi_port from .rtorrent.rc
	RTORRENT_SOCKETPATH => '',
	## path where srr files can be saved temporarly
	SRRFILEPATH => '/tmp',
	## pyrescene.py command. if not found in PATH, use something like: python /path/to/executable
	PYRESCENE => 'pyrescene.py',
	## your username for srrdb. leave blank to upload anonymously
	SRRUSERNAME => '',
	## your password for srrdb. leave blank to upload anonymously
	SRRPASSWORD => '',
	## file where to log errors and the result of srr upload. leave blank to disable
	DEBUGLOG => '',
};

## configure logging behavior
my $logpath = DEBUGLOG;
my $logger;
if ($logpath) {
    my $conf = qq(
        log4perl.category         = DEBUG, Logfile
        log4perl.appender.Logfile           = Log::Log4perl::Appender::File
        log4perl.appender.Logfile.filename  = $logpath
        log4perl.appender.Logfile.mode      = append
        log4perl.appender.Logfile.syswrite  = 1
        log4perl.appender.Logfile.TZ          = PST
        log4perl.appender.Logfile.layout = Log::Log4perl::Layout::PatternLayout
        log4perl.appender.Logfile.DatePattern = yyyy-MM-dd
        log4perl.appender.Logfile.layout.ConversionPattern = \%d{yyyy.MM.dd HH:mm::ss} \%p> \%M \%F{1}:\%L \%C \%c \%m\%n
    );

    # Initialize logging behavior
    Log::Log4perl->init( \$conf );
    $logger = get_logger("rtorrentSrr");
}

_log("You need to define an existing file path to save the srr files which is readable and writable for the executing user!", 1, 1) unless SRRFILEPATH && -d -r -w SRRFILEPATH;

my ($infohash, $basepath) = @ARGV;

my $rt = RTPG->new(url => RTORRENT_SOCKETPATH);
my ($filelist, $error) = $rt->file_list($infohash);
_log($error, 1, 1) if $error;
## get releasename from foldername rather than from rtorrent as it might differ
my ($releasename) = fileparse($basepath);

if (isValid($filelist)) {
	system(PYRESCENE." -y --best -r $basepath -o ".SRRFILEPATH);
	if (-f SRRFILEPATH."/$releasename.srr") {
		my $mech = LWP::UserAgent->new;
		$mech->post('https://www.srrdb.com/account/login', { username => SRRUSERNAME, password => SRRPASSWORD }) if SRRUSERNAME && SRRPASSWORD;
		my $result = $mech->post('https://www.srrdb.com/upload', Content_Type => 'form-data', Content => [ file => [ SRRFILEPATH."/$releasename.srr" ], upload => 'upload' ]);
		_log($result->decoded_content =~ m!<tr title="(.+)" class="color-\d">!);
		unlink SRRFILEPATH."/$releasename.srr" or _log('Could not remove '.SRRFILEPATH."/$releasename.srr: $!", 1);
	} else {
		_log("srr file could not be created for $basepath", 1, 1);
	}
}

## check if release contains a sfv file and is not from a known p2p group releasing with sfv
sub isValid {
	for (@$filelist) {
    	return 1 if $_->{path} =~ m!\.sfv$!i && $_->{path} !~ m!Z3BR4/!;
	}
    return 0;
}

## logs messages if $logger is defined
sub _log {

    my ($msg, $iserror, $die) = @_;

    if ($logger) {
        if ($iserror) {
            $logger->error($msg);
        } else {
            $logger->info($msg);
        }
    }
	die $msg if $die;
}

## destructor for the logger
sub DESTROY {

    my $self = shift;

    if ($self->{last_message_count}) {
        print "[$self->{last_message_count}]: " . "$self->{last_message}";
        return;
    }
}