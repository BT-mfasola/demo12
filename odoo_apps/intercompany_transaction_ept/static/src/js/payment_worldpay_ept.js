odoo.define('payment_worldpay_ept.worldpay', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    function worldpay_payment_submit (clientkey) {
        Worldpay.useTemplateForm({
          'clientKey':clientkey,
          'form':'paymentFormworldpay',
          'paymentSection':'wk_woldpayPaymentSection',
         'display':'inline',
          'saveButton':false,
          'type':'card',
          'callback': function(obj) {
            if (obj && obj.token) {
              submit_payment_worldpay(obj.token)          
            }
            else{
              alert('please try again');
            }
          }
        });
     }

	function submit_payment_worldpay(token) {
		$('#ept_worldpay_myModal').modal('hide');
		var payment_form = $('.o_payment_form');
		payment_form.append('<div class="payment_ept_worldpay_loader" style="display:block;position: fixed;top:0;left:0;right:0;bottom:0;background: rgba(0,0,0,0.5);z-index:9999;"><svg x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve" style=" width: 100px;height: 100px;margin: 20% auto 0;display:block;"><path fill="#fff" d="M73,50c0-12.7-10.3-23-23-23S27,37.3,27,50 M30.9,50c0-10.5,8.5-19.1,19.1-19.1S69.1,39.5,69.1,50"><animateTransform attributeName="transform" attributeType="XML" type="rotate"dur="1s" from="0 50 50"to="360 50 50" repeatCount="indefinite" /></path></svg></div>')
	    var $form = $("input[name='worldpay_client_key']").parent('form');
	  	$form.attr('action','/payment/worldpay/feedback')   
	  	var $input = $('<input type=hidden name=worldpayToken />').val(token);
	  	$form.append($input);
	  	$form.submit();
	}
	
	require('web.dom_ready');
    if (!$('.o_payment_form').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_payment_form'");
    }
    
	$('#submit_ept_worldpay_payment').on('click',function(){
          Worldpay.submitTemplateForm();
	});
	
    $.getScript("https://cdn.worldpay.com/v1/worldpay.js", function() {
   		$('#ept_worldpay_myModal').appendTo('body').modal('show');
    	
   		//Bootstrap Model Close Event 
   		$("#ept_worldpay_myModal").on('hidden.bs.modal', function () {
   		    $("#ept_worldpay_myModal").remove(); //remove model
   		    $('.modal-backdrop').remove();
   		    $("input[name='worldpay_client_key']").parent("form[provider='worldpay']").remove(); //remove Form
   		});
   		
   		var worldpay_client_key = $("input[name='worldpay_client_key']").val();
    	if(worldpay_client_key && worldpay_client_key != 'dummy'){
    		worldpay_payment_submit(worldpay_client_key);
    	}
    	else{
    		alert('please configure worldpay client key')
    	}
    });
});
