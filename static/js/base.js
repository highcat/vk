/* global globalError */
/* global ajax errors */
/* global CSRF */

// $(document).ajaxSuccess(function(event, jqXHR, ajaxSettings, data) {
//     globalError({body: 'success! ' + JSON.stringify(ajaxSettings.context)});
// });

$(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
    var silence = false;
    if (ajaxSettings.context) {
        // silence global error dialog
        var ss = ajaxSettings.context.silenceStatuses;
        silence = (ss && jqXHR.status in ss);
    }
    if (!silence) {
        switch (jqXHR.status) {
        case 400:
            globalError({
                title: '400: Ошибка ввода данных.\n'+jqXHR.responseText,
                body: jqXHR.statusText + "<br>" + jqXHR.responseText,
            });
            break;
        case 401:
            globalError({
                title: '401: Вы не авторизованы.\n\nПопробуйте обновить страницу.',
                body: "Please try to <a href='/account/login'>log in</a> or <a href='/account/signup'>sign up</a>",
            });
            break;
        case 403:
            globalError({
                title: '403: Доступ запрещён.\n\nОбновите страницу, и попробуйте снова.',
                body: "Please try to <a href='/account/login'>log in with a differen user name</a>, if you had access to this feature before.",
            });
            break;
        case 404:
            globalError({
                title: '404: Ресурс не найден.\n\nПопробуйте обновить страницу.',
                body: "Item is not found. Please try refreshing the page.",
            });
            break;
        case 409:
            globalError({
                title: '409: Unable to finish this action',
                body: "Please try refreshing the page.",
            });
            break;
        case 500:
            globalError({
                title: '500: Что-то пошло не так.\nПопробуйте повторить или перезагрузить страницу.\n\nНаши сотрудники уже узнали об ошибке, и работают над её устранением.',
                body: "We've been notified of the problem and will do our best to make sure it doesn't happen again! <br><br> Please try refreshing the page.",
            });
            break;
        case 501:
            globalError({
                title: '501: Функция не реализована!\n\nПопробуйте обновить страницу.',
                body: "This feature is not implemented yet! <br> Please try doing something else.",
            });
            break;
        case 502:
            globalError({
                title: '502: Сайт временно недоступен.\nПопробуйте повторить через несколько секунд.',
                body: "Our servers are temporarily unavailable. <br>Possibly we're updating something. <br><br>Please try again in 30 seconds.",
            });
            break;
        case 504:
            globalError({
                title: '504: Сайт временно недоступен.\nПопробуйте повторить через несколько секунд.',
                body: 'Our servers were thinking for too long.<br>Please try again, or try refreshing the page.',
            });
            break;
        default:
            globalError({
                title: 'Ошибка '+jqXHR.status + '\n\nПопробуйте обновить страницу.',
                body: 'Something wrong happened.<br>Please try again.',
            });
        }
    }
});

/* Mandatory for IE (it caches Ajax GET requests) */
$.ajaxSetup({
    cache: false,
});

// Django CSRF for Ajax POST requests
// see https://docs.djangoproject.com/en/1.3/ref/contrib/csrf/#csrf-ajax
$(document).ajaxSend(function(event, xhr, settings) {
	function getCookie(name) {
		var cookieValue = null;
		if (document.cookie && document.cookie != '') {
			var cookies = document.cookie.split(';');
			for (var i = 0; i < cookies.length; i++) {
				var cookie = jQuery.trim(cookies[i]);
				// Does this cookie string begin with the name we want?
				if (cookie.substring(0, name.length + 1) == (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}
	function sameOrigin(url) {
		// url could be relative or scheme relative or absolute
		var host = document.location.host; // host + port
		var protocol = document.location.protocol;
		var sr_origin = '//' + host;
		var origin = protocol + sr_origin;
		// Allow absolute or scheme relative URLs to same origin
		return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
			(url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
			// or any other URL that isn't scheme relative or absolute i.e relative.
			!(/^(\/\/|http:|https:).*/.test(url));
	}
	function safeMethod(method) {
		return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}

	if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
		xhr.setRequestHeader("X-CSRFToken", CSRF);
	}
});
