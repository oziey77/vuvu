$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var iconBox;
    var operatorImg;
    var selectedOperator;
    var operatorName;
    var amount;
    var recipient;
    var discountData;
    var discountRate = 0;
    var calculatedDiscount;
    var is_ported = "off";
    var safeBeneficiary = "off";

    // Offer loader text
    var currentOfferText = 'discount';

    setInterval(function(){
        if(currentOfferText == 'discount'){
            $("#discountLoader").fadeOut(function(){
                $("#offerLoader").css('display','block');
                currentOfferText = 'offer';
            })
        }
        else{
            $("#offerLoader").fadeOut(function(){
                $("#discountLoader").css('display','block')
                currentOfferText = 'discount';
            }) 
        }
    },3000)

    // Network operator validator
    var AirtelInitials = ['0911','0912','0907','0904','0902','0901','0812','0808','0802','0708','0701']
    var MTNInitials = ['0916','0913','0906','0903','0816','0814','0813','0810','0806','0803','0706','0704','0703','0702','0702']
    var GLOInitials = ['0915','0905','0815','0811','0807','0805','0705']
    var N9MobileInitials = ['0908','0909','0818','0817','0809']

    // Get airtime Discount
    $.ajax({
        url:'/get-airtime-discounts/',
        type:'GET',
        success:function(response){
            if(response.code == '00' ){
                discountData = response.data;
            };
        },
    });

    // 
    $("#network-selector").on('click',function(){
        // $("#network-dropdown").css("display","block");
        $("#network-dropdown").fadeIn();
        iconBox = $(this).find('#selectedOperatorImg')[0];
        operatorImg = $(this).find('img')[0];
        operatorName = $(this).find('p')[0];
    })
    // Select Operator
    $(".mobile-operator").on('click',function(){
        selectedOperator = $(this).attr('network-data');
        var selectedOperatorImg = $(this).attr('image-data');
        $(".operator-text").html(selectedOperator);
        $(operatorImg).attr('src',selectedOperatorImg);
        $("#selectedOperatorImg").css('display','block');
        $("#network-dropdown").fadeOut();

        // Set Operator discount
        $.each(discountData,function(key,value){
            if(value.networkOperator == selectedOperator){
                discountRate = Number(value.rate)
            };
            
        });

        // calculate discount
        discountCalculator();
        
        if (inputValid()){
            $("#buyAirtime").removeClass('disabled');
        }
        else{
            $("#buyAirtime").addClass('disabled');
        }
    });

    // Phone Number Input Logic
    $("#phone_number").bind('focusout keyup',function(){
        if (inputValid()){
            $("#buyAirtime").removeClass('disabled');
        }
        else{
            $("#buyAirtime").addClass('disabled');
        }
    });

    // Number is ported
    $("#is_ported").on("click",function(){
        if(is_ported == "off"){
            is_ported = "on";
        }
        else{
            is_ported = "off"; 
        }
        $('#error-message').text(``)
        $('.error-feedback').css('display','none')
    })

    // Amount
    $("#amount").bind('focusout keyup',function(){
        let input = $(this);
        let amount = Number(input.val());
        input.text(amount.toLocaleString());
        // Calculate discount
        discountCalculator();
        if (inputValid()){
            $("#buyAirtime").removeClass('disabled');
        }
        else{
            $("#buyAirtime").attr('disabled',true);
            $("#buyAirtime").addClass('disabled');
        };
    });

    // Toggle button activity
    $("#buyAirtime").on('click',function(e){
        e.preventDefault();        
        
        if(recipientValid() || (!recipientValid() && is_ported == "on")){
            $('#error-message').text(``)
            $('.error-feedback').css('display','none')
            $(this).attr('disabled',true);
            amount = $("#amount").val();
            recipient = $("#phone_number").val();

            $("#networOperator").html(selectedOperator.toUpperCase())
            $("#recipient").html(recipient);
            $("#airtimeAmount").html(Number(amount).toLocaleString());
            $("#cashback").html(Number(calculatedDiscount).toLocaleString());  
            $("#total").html(Number(amount).toLocaleString());        
            $("#billSummary").css("display",'block');
        }
        
    })

    // 
    $("#saveBeneficiary").on("click",function(){
        if(safeBeneficiary == "off"){
            safeBeneficiary = "on";
        }
        else{
            safeBeneficiary = "off"; 
        }
    })

    //Beneficiary clicked
    $(".save-beneficiary").on('click',function(){
        let beneficiaryData = $(this).attr('data').split('|');
        iconBox = $("#network-selector").find('#selectedOperatorImg')[0];
        operatorImg = $("#network-selector").find('img')[0];
        operatorName = $("#network-selector").find('p')[0];
        $(`a[network-data="${beneficiaryData[0]}"]`).trigger('click')
        $("#phone_number").val(beneficiaryData[1])
        $("#beneficiaryModal").css('display','none')
    })


    // Purchase Airtime
    $("#purchaseAirtime").click(function(){
        $(".error-feedback").css('display','none');
        let button = $(this)
        button.attr('disabled',true);        
        // getTransactionPin()
        buyAirtime()
        
    });

    // Cancel Transaction
    $(".cancelTrans").on('click',function(){
        $(".error-feedback").css('display','none');
        $("#buyAirtime").attr('disabled',false);
        $("#billSummary").fadeOut();
    });

    // Beneficiary Modal
    $(".open-beneficiary").on('click',function(){
        $("#beneficiaryModal").css('display','block')
    })

    // Operator Validation
    function recipientValid(){
        console.log("function called");
        let pNum = $('#phone_number').val().substring(0,4)
        if (selectedOperator == 'Airtel'){
            if(jQuery.inArray(pNum, AirtelInitials) == -1) {
                $('#error-message').html(`Please enter a valid Airtel number`)
                $('.error-feedback').css('display','block')
                // setTimeout(function(){
                //     $('.validation').css('display','none')
                // },3000)
                return false
            }
            else{
                return true
            }
            
        }
        if (selectedOperator == 'MTN'){
            if(jQuery.inArray(pNum, MTNInitials) == -1) {
                $('#error-message').text(`Please enter a valid MTN number`)
                $('.error-feedback').css('display','block')
                // setTimeout(function(){
                //     $('.validation').css('display','none')
                // },3000)
                return false
            }
            else{
                return true
            }
            
        }
        if (selectedOperator == 'Glo'){
            if(jQuery.inArray(pNum, GLOInitials) == -1) {
                $('#error-message').text(`Please enter a valid Glo number`)
                $('.error-feedback').css('display','block')
                // setTimeout(function(){
                //     $('.validation').css('display','none')
                // },3000)
                return false
            }
            else{
                return true
            }
           
        }
        if (selectedOperator == '9Mobile'){
            if(jQuery.inArray(pNum, N9MobileInitials) == -1) {
                $('#error-message').text(`Please enter a valid 9Mobile number`)
                $('.error-feedback').css('display','block')
                // setTimeout(function(){
                //     $('.validation').css('display','none')
                // },3000)
                return false
            }
            else{
                return true
            }
            
        }
    }


    // Input field validation
    function inputValid(){
        let phoneNum = $("#phone_number").val();
        let amount = Number($("#amount").val());
        if($(".operator-text").html() != "Select a network"){
            if(phoneNum.length == 11 && amount >= 50 ){
                $("#buyAirtime").attr('disabled',false);
                return true;
            }
            else{
                $("#buyAirtime").attr('disabled',true);
                return false;
            }
        }
        else{
            $("#buyAirtime").attr('disabled',true);
            return false    ;        
        }
        
    };

    // Discount calculator
    function discountCalculator(){
        let amount = $("#amount").val();
        calculatedDiscount = ((amount * discountRate ) / 100).toFixed(2)
        $(".calculatedDiscount").html(calculatedDiscount)
        $(".discount-container").css('display','block')
    };

    // Get transaction pin function
    function getTransactionPin(){
        $('#PINValidation').fadeIn()
        $(function(){
            $('#PINWrapper').pinlogin({
              fields : 4, // default 5
              placeholder:'*', // default: '•'
              reset :false,
              complete :function(pin){
                console.log(pin)
                buyAirtime(transcationPin=pin)
                  },
            });
          })
    }

    function buyAirtime(){   
        // $("#PINValidationError").html('')
        // $("#PINValidationError").css('display','none');     
        $(".loader-overlay").css('display','flex');
        $.ajax({
            url:'/purchase-airtime/',
            type:'POST',
            headers: {'X-CSRFToken': $crf_token},
            data:{
                "operator":selectedOperator,
                "recipient":recipient,
                "amount":amount,
                "safeBeneficiary":safeBeneficiary
            },
            success:function(response){
                console.log(response)
                if( response.code == '00' ){  
                    // $("#PINValidation").css("display","none");                  
                    $("#billSummary").fadeOut(function(){
                        $(".loader-overlay").css('display','none');
                        $("#transactionFeedback").css("display",'block');
                    });
                    

                }
                else if(response.code == '01'){
                    $("#PINValidationError").html(response.message)
                    $("#PINValidationError").css('display','block');
                    $("#purchaseAirtime").attr('disabled',false);
                }
                else if(response.code == '09'){
                    $(".error-message").html(response.message);
                    // $(".error-feedback").slideUp()
                    $(".error-feedback").css('display','block');
                    $("#purchaseAirtime").attr('disabled',false);
                    // $('#PINValidation').fadeOut()
                };
                $(".loader-overlay").css('display','none');
            }
        });
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target.id == "PINValidation" || event.target.id == 'closePINValidation' || event.target.id == 'transactionFeedback' || event.target.id == 'billSummary') {
            // $("#PINValidation").css("display","none");
            // $(".setting-modal").css("display","none");
            
        }
        else if(event.target.id == "beneficiaryModal"){
            $("#beneficiaryModal").css('display','none')
        }
    };

});