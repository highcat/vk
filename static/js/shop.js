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


  _.each($('.side-panel'), function(el){
    var $el = $(el);
    // manager's panel
    var PANEL_HIDE_LEN = $el.outerWidth() - 5;
    var myStorage = window.localStorage;
    var panelId = $el.data('panel-id');
    var defaultOpened = $el.data('default-opened') || null;
    _l(defaultOpened)

    if (!(myStorage.getItem('managerPanelOpened-'+panelId))) {
      myStorage.setItem('managerPanelOpened-'+panelId, defaultOpened);
    }
    _l('---', myStorage.getItem('managerPanelOpened-'+panelId));
    
    var onClosePanel = function(){
      $el.find('.side-panel_control .close').hide();
      $el.find('.side-panel_control .open').show();
      myStorage.setItem('managerPanelOpened-'+panelId, 'no');
    };
    var closePanel = function(){
      $el.animate({left: '-'+PANEL_HIDE_LEN+'px'}, 200, 'swing', onClosePanel);
    };
    var onShowPanel = function(){
      $el.find('.side-panel_control .close').show();
      $el.find('.side-panel_control .open').hide();
      myStorage.setItem('managerPanelOpened-'+panelId, 'yes');
    };
    var showPanel = function(){
      $el.animate({left: '0px'}, 200, 'swing', onShowPanel);
    };
    
    $el.find('.side-panel_control .close').on('click', closePanel);
    $el.find('.side-panel_control .open').on('click', showPanel);

    var v = myStorage.getItem('managerPanelOpened-'+panelId);
    if (v == 'yes') {
      onShowPanel();
    } else {
      $el.css({left: '-'+PANEL_HIDE_LEN+'px'});
      onClosePanel();
    }
  });
});
