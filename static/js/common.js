/* global USER_LOGGED_IN, USER_GROUPS, USER_IS_ADMIN */
/* exported globalSuccess, globalError, globalConfirm, askForLogIn, askForLogInNow */

$(function(){
    $('#global-message-dialog').modal({'show': false});
});

var globalError = function(conf) {
    alert(conf.title);
    // var $el = $('#global-message-dialog');
    // $el.find('.modal-title').text(conf.title || 'Error');
    // $el.find('.modal-body').html(conf.body || 'Oops!<br>Something wrong happened.');
    // $el.find('.btn-role-submit').hide();
    // $el.find('.btn-role-submit').unbind('click');
    // $el.modal('show');
};

var globalSuccess = function(conf) {
    var $el = $('#global-message-dialog');
    $el.find('.modal-title').text(conf.title || 'Success');
    $el.find('.modal-body').html(conf.body || 'Action completed.');
    $el.find('.btn-role-submit').hide();
    $el.find('.btn-role-submit').unbind('click');
    $el.modal('show');
};

var globalConfirm = function(conf) {
    var $el = $('#global-message-dialog');
    $el.find('.modal-title').text(conf.title || 'Confirm');
    $el.find('.modal-body').html(conf.body || 'Are you sure you want to perform this action?');
    $el.find('.btn-role-submit').text(conf.buttonText || 'Ok');
    $el.find('.btn-role-submit').show();
    $el.find('.btn-role-submit').unbind('click');
    $el.find('.btn-role-submit').bind('click', conf.callback || function(){});
    $el.modal('show');
};
