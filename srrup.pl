#!/usr/bin/perl

use strict;
use warnings;
use v5.10;

use WWW::Mechanize;
use HTTP::Request::Common;
use HTML::TreeBuilder::XPath;

my $username = '';
my $password = '';

if (@ARGV < 1) {
  say STDERR "Usage: $0 file.srr [file.srr...]";
  exit 1;
}

my @files = @ARGV;

my $mech = WWW::Mechanize->new;  
$mech->post('http://www.srrdb.com/account/login', {
  username => $username,
  password => $password,
});

foreach (@files) {
  upload_srr($_);
};


sub upload_srr {
  my $file = shift;
  
  my $req = $mech->request(POST 'http://www.srrdb.com/upload', 
    Content_Type => 'form-data',
    Content => {
      file => [ $file ],
      upload => 'upload',
  });

  my $tree = HTML::TreeBuilder::XPath->new_from_content($req->decoded_content)->elementify;
  
  my $error = $tree->findvalue('//span[@class="error"]');
  if ($error) {
    say STDERR $error;
    exit 1;
  }

  say $tree->findvalue('//div[@class="oflow wName"');
}
