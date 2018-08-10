/* global _, _l, Mn, Backbone */
/* global globalConfirm, globalMessage */
/* global USER_LOGGED_IN, USER_IS_ADMIN */
$(function(){
    var Mn = Backbone.Marionette;
    if ($('#opCalendarModal').length) {
        $('#opCalendarModal').on('shown.bs.modal', function(e){
            var DayModel = Backbone.Model.extend({
                idAttribute: 'day',
            });
            var DayCollection = Backbone.Collection.extend({
                url: '/api/v1/op-days/',
                model: DayModel,
            });
            
            var View = Mn.View.extend({
                template: '#op-calendar-template',
                events: {
                    'click [data-day]': 'onClickDate',
                    'contextmenu [data-day]': 'onAltClickDate',
                },
                collectionEvents: {
                    'sync': 'onNewDatesMarks',
                },
                onRender: function(){
                    this.$('.datetime-picker').datetimepicker({
                        inline: true,
                        showTodayButton: false,
                        sideBySide: false,
                    });
                    this.onNewDatesMarks();
                },
                onNewDatesMarks: function(){
                    var d = {};
                    this.collection.each(function(model, idx){
                        d[model.id] = model.get('status');
                    });
                    this.$('.datetime-picker').datetimepicker('datesMarks', d);
                },
                onClickDate: function(e){
                    if (!USER_IS_ADMIN) {
                        return;
                    }
                    var $el = $(e.currentTarget);
                    var day = $el.data('day');
                    var hasStatus = $el.hasClass('mark-closed');
                    var self = this;
                    $.ajax({
                        type: hasStatus ? 'delete': 'put',
                        url: '/api/v1/op-days/'+day+'/status/closed/',
                        dataType: 'json',
                        processData: false,
                        contentType: 'application/json',
                    }).done(function(data){
                        self.collection.fetch();
                    });
                },
                onAltClickDate: function(e){
                    if (!USER_IS_ADMIN) {
                        return;
                    }
                    e.preventDefault();
                    var $el = $(e.currentTarget);
                    var day = $el.data('day');
                    var hasStatus = $el.hasClass('mark-open');
                    var self = this;
                    $.ajax({
                        type: hasStatus ? 'delete': 'put',
                        url: '/api/v1/op-days/'+day+'/status/open/',
                        dataType: 'json',
                        processData: false,
                        contentType: 'application/json',
                    }).done(function(data){
                        self.collection.fetch();
                    });
                },
            });
            
            var collection = new DayCollection();
            var view = new View({
                el: $('.op-calendar-placeholder')[0],
                collection: collection,
            });
            collection.once('sync', function(){
                view.render();
            });
            collection.fetch();            
        });            
    }
});
