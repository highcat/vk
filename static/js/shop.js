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
});
