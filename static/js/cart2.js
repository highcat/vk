/* global _, _l, Mn, Backbone */
/* global globalConfirm, globalMessage */
/* global USER_LOGGED_IN, USER_IS_ADMIN */
/* global ga */

$(function(){
    var Mn = Backbone.Marionette;

    // Storage, for now just using `localStorage` and ignoring old browser that doesn't
    // support it, later will be updated to support older browsers also.
    var db = {
        get    : function(key){return window.localStorage.getItem(key);},
        set    : function(key, value){window.localStorage.setItem(key, value);},
        remove : function(key){window.localStorage.removeItem(key);}
    };

    var DEFAULT_ORDER_MODEL = {
        // XXX adding a new item here RESETS all users' carts.
        items: [],
        items_price: 0, // w/o discounts
        total_price: 0,
        promo_code: '',
        contact_name: '',
        contact_phone: '',
        contact_email: '',
        contact_address: '',
        delivery: '',
        note: '',
        discounts: {variable: 0, fixed: 0, names: []},
        errors: {},
        warnings: {},
    };

    if ($('.cart-placeholder').length) {
        /****************************** Model classes *************************/
        var OrderCompleteModel = Backbone.Model.extend({});
        var OrderModel = Backbone.Model.extend({});
        var CartItemsCollection = Backbone.Collection.extend({
            initialize: function(models, options){
                this.on('change', this._modelChanged, this);
            },
            _modelChanged: function(model, value){
                this.trigger('childChanged');
            },
        });


        /****************************** Creating models *************************/
        var orderModel = new OrderModel({});
        var orderCompleteModel = new OrderCompleteModel({});
        var cartItemsCollection = new CartItemsCollection([]);

        /****************************** Controllers *************************/
        // Save to local storage
        orderModel.listenTo(orderModel, 'change', function(){
            db.set('order-data', JSON.stringify(orderModel.attributes));
        });
        var updateOrderModel = function(){
            // XXX saving to model silently
            var items_price = _.reduce(
                _.map(cartItemsCollection.models, function(m){ 
                    return (m.get('discount_price') || m.get('price')) * m.get('count');
                }),
                function(a,b){ return a+b; }
            );
            var total_price = items_price;
            // Count, same to backend
            total_price *= (1.0-(orderModel.get('discounts').variable / 100));
            total_price -= orderModel.get('discounts').fixed;
            total_price = Math.floor(total_price);
            
            orderModel.set({
                items: cartItemsCollection.toJSON(),
                items_price: items_price,
                total_price: total_price,
            });
        };
        cartItemsCollection.listenTo(cartItemsCollection, 'update childChanged', updateOrderModel);

        // Send information entered by user,
        // and update prices & discounts from server.
        var updateOrderFromServer = function(options, cb){
            if (options === undefined) {
                options = {
                    silentErrors: false,
                };
            }
            var silenceStatuses = {};
            if (options.silentErrors) {
                /* suppress temporary errors */
                silenceStatuses = {0: true, 500: true, 504: true, 503: true};
            }

            $.ajax({
                type: 'post',
                url: '/api/v1/order/update/',
                data: JSON.stringify(orderModel.toJSON()),
                dataType: 'json',
                processData: false,
                contentType: 'application/json',
                context: {silenceStatuses: silenceStatuses},
            }).done(function(data){
                orderModel.set(data);
                orderModel.trigger('sync');
                cartItemsCollection.reset(orderModel.get('items'));
                if (cb) {
                    cb();
                }
            });
        };


        /****************************** Views *************************/
        var CartButtonView = Mn.View.extend({
            template: '#cart-button-template',
            events: {
                click: 'onClick',
            },
            initialize: function(){
                this.listenTo(this.collection, 'childChanged', this.render);
                this.listenTo(this.collection, 'update', this.render);
                this.listenTo(this.collection, 'reset', this.render);
            },
            onClick: function(e){
                e.preventDefault();
                cartPopupView.toggle();
            },
            onRender: function(){
                this.$('.cart-button').addClass('just-changed');
                setTimeout(function(){
                    this.$('.cart-button').removeClass('just-changed');
                }, 100);
            },
            serializeData: function(){
                var d = {};
                d.items = this.collection.toJSON();
                var l = d.items.length;
                if (l in {11: 1, 12: 1, 13: 1, 14: 1}) {
                    d.label = 'товаров';
                } else {
                    var lastDigit = (''+l)[(''+l).length-1];
                    d.label = {
                        '0': 'товаров',
                        '1': 'товар',
                        '2': 'товара',
                        '3': 'товара',
                        '4': 'товара',
                        '5': 'товаров',
                        '6': 'товаров',
                        '7': 'товаров',
                        '8': 'товаров',
                        '9': 'товаров',
                    }[lastDigit];
                }
                return d;
            },
        });

        var CartPopupView = Mn.View.extend({
            template: '#cart-popup-template',
            events: {
                'click .cart-hide > a': 'onHide',
                'click .cart-clear > a': 'onClear',
            },
            regions: {
                cart: '.cart-region',
                orderForm: '.order-form-region',
                orderSent: '.order-sent-region',
            },
            serializeData: function(){
                var d = {};
                d.items = this.collection.toJSON();
                d.order = this.model.toJSON();
                d.USER_IS_ADMIN = USER_IS_ADMIN;
                return d;
            },
            initialize: function(options){
                // this.listenTo(this.collection, 'childChanged', this.onCountUpdated);
                this.listenTo(this.collection, 'update', this.onCountUpdated);
                this.listenTo(this.collection, 'reset', this.onCountUpdated);

                this._childViews = {};
                this._childViews.cart = new CartView({model: this.model, collection: this.collection});
                this._childViews.orderForm = new OrderFormView({model: this.model});
                this._childViews.orderSent = new OrderSentView({model: orderCompleteModel});
            },
            onHide: function(e){
                e.preventDefault();
                this.$el.addClass('hide');
            },
            onClear: function(e){
                e.preventDefault();
                db.remove('order-data');
                location.reload();
            },
            onBeforeRender: function(){
                var self = this;
                _.each(this.regions, function(val, key){ self.detachChildView(key); });
            },
            onCountUpdated: function(){
                // XXX need view state model here
                if (this.collection.length === 0) {
                    this.$(".cart-region").addClass('hide');
                    this.$(".cart-empty-message").removeClass('hide');
                } else {
                    this.$(".cart-region").removeClass('hide');
                    this.$(".cart-empty-message").addClass('hide');
                }
            },
            onRender: function(){
                // Fix height, if too long
                this.$el.scrollTop(0);
                this.showChildView('cart', this._childViews.cart);
                this.showChildView('orderForm', this._childViews.orderForm);
                this.showChildView('orderSent', this._childViews.orderSent);
                this.limitMaxSize();
            },
            hide: function(){
                this.$el.addClass('hide');
            },
            show: function(){
                this.$el.removeClass('hide');
                // go to 1st page
                this.setVisiblePage('cart');
                this.limitMaxSize();
            },
            limitMaxSize: function() {
                if (this.$el.position().top + this.$el.height() > $(window).height()-5) {
                    this.$el.css('bottom', '5px');
                }
            },
            toggle: function(){
                if (this.$el.hasClass('hide')) {
                    this.show();
                } else {
                    this.hide();
                }
            },
            onChildviewReadyToOrder: function(){
                this.setVisiblePage('orderForm');
            },
            onChildviewBackClicked: function(){
                this.setVisiblePage('cart');
            },
            onChildviewOrderSent: function(){
                this.setVisiblePage('orderSent');
            },
            setVisiblePage: function(page){
                switch(page) {
                case 'cart':
                    this.$('.cart-region').removeClass('hide');
                    this.$('.order-form-region').addClass('hide');
                    this.$('.order-sent-region').addClass('hide');
                    break;
                case 'orderForm':
                    this.$('.cart-region').addClass('hide');
                    this.$('.order-form-region').removeClass('hide');
                    this.$('.order-sent-region').addClass('hide');
                    break;
                case 'orderSent':
                    this.$('.cart-region').addClass('hide');
                    this.$('.order-form-region').addClass('hide');
                    this.$('.order-sent-region').removeClass('hide');
                    break;
                }
            },
        });


        var CartItemView = Mn.View.extend({
            template: '#cart-item-template',
            events: {
                'change .cart-item-count': 'onCountChange',
                'keypress .cart-item-count': 'onCountKeyPress',
                'click .cart-item-remove': 'onRemove',
            },
            onCountKeyPress: function(e){
                if (e.which == 13) {
                    this.onCountChange();
                }
            },
            onCountChange: function(){
                var q = parseInt(this.$('.cart-item-count').val()) || 1;
                this.model.set({count: q});
            },
            onRemove: function(e){
                e.preventDefault();
                this.triggerMethod('removeMe', this); // Marionette's triggerMethod, bubbled to `onChildviewRemoveMe`
            },
        });


        var CartView = Mn.CompositeView.extend({
            template: '#cart-template',
            childViewContainer: '.items-region',
            childView: CartItemView,
            events: {
                'click .cart-purchase-button': 'onPurchase',
                'click .warn-close': 'onWarnClose',
                'change [name=code]': 'onCodeChange',
                'keydown [name=code]': 'onCodeKeyDown',
            },
            serializeData: function(){
                var d = {};
                d.items = this.collection.toJSON();
                d.order = this.model.toJSON();
                return d;
            },
            initialize: function(options){
                this.listenTo(this.model, 'change', this.render);
                this.listenTo(this.collection, 'childChanged', this.render);
                this.listenTo(this.collection, 'update', this.render);
                this.listenTo(this.collection, 'reset', this.render);
            },
            onChildviewRemoveMe: function(childView) {
                this.collection.remove(childView.model);
            },
            onPurchase: function(){
                this.$('.cart-purchase-button').html(_.template($('#button-spinner-template').text())());
                updateOrderFromServer({}, _.bind(function(){
                    if (!this.model.get('new_warnings') &&
                        0 === _.size(this.model.get('errors'))) {
                        this.triggerMethod('readyToOrder');
                    }
                    if (_.size(this.model.get('errors'))) {
                        alert('Ошибка!\n\n' + JSON.stringify(this.model.get('errors')));
                    }
                }, this));
            },
            onWarnClose: function(e){
                var $el = $(e.currentTarget).parents('li');
                var key = $el.data('warn-id');
                var w = orderModel.get('warnings');
                delete w[key];
                orderModel.set('warnings', w);
                orderModel.trigger('change', orderModel); // XXX
            },
            onCodeKeyDown: function(e){
                if (e.which == 13) {
                    this.onCodeChange({force: true});
                }
            },
            onCodeChange: function(options){
                if (options === undefined) {
                    options = {force: false};
                }
                var oldCode = $.trim(this.model.get('code'));
                var code = $.trim(this.$('[name=code]').val());
                if (oldCode != code || options.force) {
                    this.model.set({'code': code}, {'silent': true});
                    updateOrderFromServer(); // get discount and update price
                }
            },
        });


        var OrderFormView = Mn.View.extend({
            template: '#cart-order-form-template',
            events: {
                'click .cart-back-button': 'onBack',
                'click .cart-send-order-button': 'onSendOrder',
                'change [name=delivery]': 'updateDelivery',
                'change [name]': 'saveDataFromDOM',
                'click .warn-close': 'onWarnClose',
            },
            serializeData: function(){
                var d = {};
                d.order = this.model.toJSON();
                return d;
            },
            initialize: function(options){
                this.listenTo(this.model, 'change', this.render);
                this.listenTo(this.collection, 'childChanged', this.render);
                this.listenTo(this.collection, 'update', this.render);
                this.listenTo(this.collection, 'reset', this.render);
            },
            onRender: function(){
                this.updateDelivery();
                _.each(this.model.get('errors', {}), _.bind(function(val, key){
                    this.$('[name='+key+']').parents('.form-group').addClass('has-error');
                }, this));
            },
            onBack: function(){
                this.triggerMethod('backClicked');
            },
            updateDelivery: function(){
                var val = this.$('[name=delivery]:checked').val() || ''; // NOT undefined
                this.model.set({delivery: val});
                this.$('.delivery-option').hide();
                this.$('[data-d-type="'+val+'"]').show();
            },
            collectData: function(){
                var data = {};
                _.each(this.$('input[name]'), function(el){
                    data[$(el).attr('name')] = $(el).val();
                });
                data.delivery = this.$('[name=delivery]:checked').val() || ''; // NOT undefined
                data.contact_address = this.$('[name=contact_address]').val();
                data.accept_for_ads = this.$('[name=accept-for-ads]').is(':checked');
                data.op_phone_order = this.$('[name=op-phone-order]').is(':checked')  || '';
                data.status_confirmed = this.$('[name=status-confirmed]').is(':checked')  || '';
                return data;
            },
            saveDataFromDOM: function(){
                this.model.set(this.collectData());                
            },
            onSendOrder: function(){
                this.$('.cart-send-order-button').html(_.template($('#button-spinner-template').text())());
                orderModel.set(this.collectData(), {silent: true});
                $.ajax({
                    type: 'post',
                    url: '/api/v1/order/complete/',
                    data: JSON.stringify(orderModel.toJSON()),
                    dataType: 'json',
                    processData: false,
                    contentType: 'application/json',
                }).done(_.bind(function(data){
                    this.model.set(data);
                    if (data.new_warnings || _.size(data.errors)) {
                        this.render();
                        return;
                    }
                    if (data.order_sent) {
                        orderCompleteModel.set(this.model.attributes);
                        this.triggerMethod('orderSent');
                        this.model.clear({silent: true});
                        cartItemsCollection.reset([]);
                        this.model.set(DEFAULT_ORDER_MODEL);
                    }

                    if (data.order_sent) {
                        if (typeof(ga) !== "undefined") {
                            ga('require', 'ecommerce', 'ecommerce.js');
                            ga('ecommerce:addTransaction', {
                                // ID транзакции
                                'id': data.order_id,
                                // Название магазина
                                'affiliation': 'vkusnyan.ru',
                                // Общая стоимость заказа
                                'revenue': data.total_price,
                                // Стоимость доставки
                                'shipping': 0, // XXX
                                // Налог
                                'tax': '',
                            });
                            _.each(data.ua_items, function(ua_i){
                                // уже собрано на бэкэнде
                                ga('ecommerce:addItem', ua_i);
                            });
                            ga('ecommerce:send');
                            // Шлём доп. событие для достижения цели
                            ga('send', {
                                hitType: 'event',
                                eventCategory: 'Ecommerce',
                                eventAction: 'order1',
                                // eventLabel: 'Fall Campaign'
                            });
                        }
                        if (window.yaCounter39025605 !== undefined) {
                            // window.dataLayer.push({
                            //     "ecommerce": {
                            //         "purchase": {
                            //             "actionField": {
                            //                 id: ''+data.order_id,
                            //                 goal_id: "24342945",
                            //             },
                            //             "products": [{
                            //                     "id": "0000",
                            //                     "name": "Dummy",
                            //                     "price": data.total_price,
                            //                     "brand": "Vkusnyan",
                            //                     "category": "All",
                            //                     "variant": "no variant"
                            //             },],
                            //         },
                            //     },
                            // });
                            window.yaCounter39025605.reachGoal('order1', {orderData: orderModel.toJSON()});
                        }
                    }
                }, this));
            },
            onWarnClose: function(e){
                var $el = $(e.currentTarget).parents('li');
                var key = $el.data('warn-id');
                var w = orderModel.get('warnings');
                delete w[key];
                orderModel.set('warnings', w);
                orderModel.trigger('change', orderModel); // XXX
            },
        });

        var OrderSentView = Mn.View.extend({
            template: '#cart-order-sent-template',
            initialize: function(options){
                this.listenTo(this.model, 'change', this.render);
            },
        });

        var AddButtonView = Mn.View.extend({
            events: {
                'click ': 'onClick',
            },
            onClick: function(e){
                e.preventDefault();
                if (this.$el.hasClass('cart-buy-button_not')) {
                    return;
                }
                var itemId = this.$el.data('id');
                var itemName = this.$el.data('name');
                var itemPrice = parseInt(this.$el.data('price'));
                var itemDiscountPrice = parseInt(this.$el.data('discount-price'));
                var finalPrice = itemDiscountPrice || itemPrice;
                var itemCount = parseInt(this.$el.prev('.cart-buy-count').val());
                if (_.isNaN(itemCount)) {
                    itemCount = 1;
                    this.$el.prev('.cart-buy-count').val(1);
                }
                var preorder = this.$el.data('preorder');
                var inCollection = cartItemsCollection.filter(function(i){ return i.id == itemId; });
                if (inCollection.length) {
                    var m = cartItemsCollection.get(itemId);
                    var count = ((m.get('count') || 0) + 1);
                    m.set({
                        count: count,
                        sum: finalPrice * count,
                    });
                } else {
                    if (window.yaCounter39025605 !== undefined) {
                        window.yaCounter39025605.reachGoal('put-to-cart1');
                    }
                    cartItemsCollection.add(new Backbone.Model({
                        id: itemId,
                        count: itemCount,
                        preorder: preorder,
                        name: itemName,
                        price: itemPrice,
                        discount_price: itemDiscountPrice,
                        sum: finalPrice * itemCount,
                    }));
                }
            },
        });


        /**************************** Creating views ****************************/
        var cartButtonTopView = new CartButtonView({
            el: $('.cart-placeholder--top'),
            collection: cartItemsCollection,
        });
        var cartButtonFixedView = new CartButtonView({
            el: $('.cart-placeholder--fixed'),
            collection: cartItemsCollection,
        });
        cartButtonTopView.render();
        cartButtonFixedView.render();

        var cartPopupView = new CartPopupView({
            el: $('.cart-widget')[0],
            model: orderModel,
            collection: cartItemsCollection,
        });
        
        $('.cart-buy-button').each(function(){
            new AddButtonView({el: this});
        });


        /**************************** Launch ****************************/
        // Load the cart
        try {
            orderModel.set(JSON.parse(db.get('order-data')));
            // validate saved fields
            var bad = false;
            _.each(DEFAULT_ORDER_MODEL, function(val, key){
                if (orderModel.get(key) === undefined) {
                    _l('bad data because of key', key);
                    bad = true;
                }
            });
            if (bad) throw new SyntaxError();
        } catch (e) {
            if (e instanceof SyntaxError) {
                _l('Error, reset the cart');
                orderModel.clear({silent: true});
                orderModel.set(DEFAULT_ORDER_MODEL);
                cartItemsCollection.reset(orderModel.get('items'));
                _l('reset done');
            }
        }
        updateOrderFromServer();
        cartPopupView.render();

        // /**************************** Periodic tasks ****************************/
        //
        // Dont need this actually. 
        // & no need to debug/fix.
        //
        // setInterval(function(){
        //     updateOrderFromServer({silentErrors: true});
        // }, 1000 * 60 * 5);
    }
});
