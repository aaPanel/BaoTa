<?php
/**
 +-------------------------------------------------------------------------+
 | Roundcube Webmail IMAP Client                                           |
 | Version 1.6.7                                                           |
 |                                                                         |
 | Copyright (C) The Roundcube Dev Team                                    |
 |                                                                         |
 | This program is free software: you can redistribute it and/or modify    |
 | it under the terms of the GNU General Public License (with exceptions   |
 | for skins & plugins) as published by the Free Software Foundation,      |
 | either version 3 of the License, or (at your option) any later version. |
 |                                                                         |
 | This file forms part of the Roundcube Webmail Software for which the    |
 | following exception is added: Plugins and Skins which merely make       |
 | function calls to the Roundcube Webmail Software, and for that purpose  |
 | include it by reference shall not be considered modifications of        |
 | the software.                                                           |
 |                                                                         |
 | If you wish to use this file in another project or create a modified    |
 | version that will not be part of the Roundcube Webmail Software, you    |
 | may remove the exception above and use this source code under the       |
 | original version of the license.                                        |
 |                                                                         |
 | This program is distributed in the hope that it will be useful,         |
 | but WITHOUT ANY WARRANTY; without even the implied warranty of          |
 | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            |
 | GNU General Public License for more details.                            |
 |                                                                         |
 | You should have received a copy of the GNU General Public License       |
 | along with this program.  If not, see http://www.gnu.org/licenses/.     |
 |                                                                         |
 +-------------------------------------------------------------------------+
 | Author: Thomas Bruederli <roundcube@gmail.com>                          |
 | Author: Aleksander Machniak <alec@alec.pl>                              |
 +-------------------------------------------------------------------------+
*/

// include environment
require_once 'program/include/iniset.php';


if (trim(rcube_utils::get_input_string('_aap_token', rcube_utils::INPUT_POST)) !== '__WEBMAIL_ROUNDCUBE_RANDOM_TOKEN__') {
    header('Location: /index.php');
}

// init application, start session, init output class, etc.
$RCMAIL = rcmail::get_instance(0, isset($GLOBALS['env']) ? $GLOBALS['env'] : null);

$auth = $RCMAIL->plugins->exec_hook('authenticate', [
        'host'  => $RCMAIL->autoselect_host(),
        'user'  => '__WEBMAIL_ROUNDCUBE_USERNAME__',
        'pass'  => '__WEBMAIL_ROUNDCUBE_PASSWORD__',
        'valid' => true,
        'error' => null,
        'cookiecheck' => true,
]);

$RCMAIL->login($auth['user'], $auth['pass'], $auth['host'], $auth['cookiecheck']);

$RCMAIL->session->remove('temp');
$RCMAIL->session->regenerate_id(false);

// send auth cookie if necessary
$RCMAIL->session->set_auth_cookie();

$RCMAIL->log_login();


// restore original request parameters
$query = [];
if ($url = rcube_utils::get_input_string('_url', rcube_utils::INPUT_POST)) {
    parse_str($url, $query);

    // prevent endless looping on login page
    if (!empty($query['_task']) && $query['_task'] == 'login') {
        unset($query['_task']);
    }

    // prevent redirect to compose with specified ID (#1488226)
    if (!empty($query['_action']) && $query['_action'] == 'compose' && !empty($query['_id'])) {
        $query = ['_action' => 'compose'];
    }
}

@unlink('__WEBMAIL_ROUNDCUBE_LOGINPHP_PATH__');

header('Location: /index.php');
