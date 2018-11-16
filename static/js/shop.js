$(function(){
  $(window).scroll(function(){
    if ($(window).scrollTop() > 150) {
      $('.header-fixed').addClass('active');
      $('.up-button').show();
    } else {
      $('.header-fixed').removeClass('active');
      $('.up-button').hide();
    }
  });

  // manager's panel
  var PANEL_HIDE_LEN = $('.manager-panel').outerWidth() - 5;
  var myStorage = window.localStorage;

  if (_.isUndefined(myStorage.getItem('managerPanelOpened'))) {
    myStorage.setItem('managerPanelOpened', 'yes');
  }
  _l(myStorage.getItem('managerPanelOpened'));
  
  var onClosePanel = function(){
    $('.manager-panel_control .close').hide();
    $('.manager-panel_control .open').show();
    myStorage.setItem('managerPanelOpened', '');
  };
  var closePanel = function(){
    $('.manager-panel').animate({left: '-'+PANEL_HIDE_LEN+'px'}, 200, 'swing', onClosePanel);
  };
  var onShowPanel = function(){
    $('.manager-panel_control .close').show();
    $('.manager-panel_control .open').hide();
    myStorage.setItem('managerPanelOpened', 'yes');
  };
  var showPanel = function(){
    $('.manager-panel').animate({left: '0px'}, 200, 'swing', onShowPanel);
  };
  
  $('.manager-panel_control .close').on('click', closePanel);
  $('.manager-panel_control .open').on('click', showPanel);

  var v = myStorage.getItem('managerPanelOpened');
  if (v) {
    onShowPanel();
  } else {
    $('.manager-panel').css({left: '-'+PANEL_HIDE_LEN+'px'});
    onClosePanel();
  }
});
