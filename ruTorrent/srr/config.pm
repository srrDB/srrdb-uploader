package config;

use strict;

## INSTALLATION

## prerequisites: pyrescene.py obviously :)

## 1. install the following two CPAN modules: RTPG and WWW::Mechanize

## 1a with root privileges:
## sudo cpan App::cpanminus
## sudo cpanm RTPG WWW::Mechanize Log::Log4perl

## 1b without root privileges:
## wget -O- http://cpanmin.us | perl - -l ~/perl5 App::cpanminus local::lib
## eval `perl -I ~/perl5/lib/perl5 -Mlocal::lib`
## echo 'eval `perl -I ~/perl5/lib/perl5 -Mlocal::lib`' >> ~/.profile
## echo 'export MANPATH=$HOME/perl5/man:$MANPATH' >> ~/.profile
## cpanm RTPG WWW::Mechanize Log::Log4perl

## 1c check out http://www.cpan.org/modules/INSTALL.html to see what other options exist

## 2. adjust webserver configs

## 2a Apache
## 2a.1 create .htaccess inside plugin folder and add the following:

## AddHandler cgi-script .pl
## Options +ExecCGI
## SetEnv PERL5LIB /path/to/perl5/lib/perl5

## the third line is only necessary, if you don't have root privileges and installed the modules
## like described in 1b. Alternatively to the .htaccess, if you are root, you can also add the
## following to your apache.conf

## <Directory /path/to/rutorrent/plugins/srr>
##   AllowOverride None
##   Options +ExecCGI
##   AddHandler cgi-script .pl
## </Directory>

## 2a.2 restart apache

## 2b lighttpd
## 2b.1 add the following to your lighttp.conf

## cgi.assign = ( ".pl" => "/usr/bin/perl" )
## setenv.add-environment = ( "PATH" => env.PATH )

## 2c nginx:
## 2c.1 no modifications necessary

## 3. check and adjust the following constants

use constant {

    ## scgi_local or scgi_port from .rtorrent.rc
    RTORRENT_SOCKETPATH => '',
    # path to pyrescene bin folder. if not provided, pyrescene.py needs to be found in PATH
    PYRESCENE_PATH => '',
    ## your username for srrdb. leave blank to upload anonymously
    SRRUSERNAME => '',
    ## your password for srrdb. leave blank to upload anonymously
    SRRPASSWORD => '',
};

1;
