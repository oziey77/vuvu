$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var iconBox;
    var operatorImg;
    var selectedOperator = '';
    var selectedOperatorName;
    var selectedOperatorImg
    var operatorName;
    var customerName 
    var amount = 0;
    var accountId = '';
    var otherData;
    var saveBeneficiary = "off";

    $(".link-nav").on("click",function(){
        $("#main-loader").css("display","flex")
      })
    // Operator Selector
    $("#operator-selector").on('click',function(){
        // $("#network-dropdown").css("display","block");
        $("#operator-dropdown").fadeIn();
        iconBox = $(this).find('#selectedOperatorImg')[0];
        operatorImg = $(this).find('img')[0];
        operatorName = $(this).find('p')[0];
    })
    // Select Operator
    $(".betting-company").on('click',function(){
        selectedOperator = $(this).attr('network-data');
        selectedOperatorImg = $(this).attr('image-data');
        selectedOperatorName = $(this).attr('disco')
        $(".operator-text").html(selectedOperatorName);
        $(operatorImg).attr('src',selectedOperatorImg);
        $("#selectedOperatorImg").css('display','block');
        $("#operator-dropdown").fadeOut();
        $("#bettingId").val('')

        // inputValid()
    });

    // Wallet ID
    $("#bettingId").bind('keyup focusout',function(){
        accountId = $(this).val()        
        inputValid()
    })

    // Meter Number
    $("#amount").bind('keyup focusout',function(){
        amount = Number($(this).val())
        inputValid()
    })

    // BENEFICIARY

    // Open Beneficiary Modal
    $(".open-beneficiary").on('click',function(){
        $("#beneficiaryModal").css('display','block');
    })
    // Save Beneficiary
    $("#saveBeneficiary").on("click",function(){
        if(saveBeneficiary == "off"){
            saveBeneficiary = "on";
        }
        else{
            saveBeneficiary = "off"; 
        }
    })

    //Beneficiary clicked
    $(".save-beneficiary").on('click',function(){
        let beneficiaryData = $(this).attr('data').split('|');
        iconBox = $("#network-selector").find('#selectedOperatorImg')[0];
        operatorImg = $("#network-selector").find('img')[0];
        operatorName = $("#network-selector").find('p')[0];
        $(`a[network-data="${beneficiaryData[0]}"]`).trigger('click')
        $("#phone_number").val(beneficiaryData[1]);
        $("#beneficiaryModal").css('display','none');
    })

    // Buy electricity
    $("#fundBetting").on('click',function(e){
        e.preventDefault()
        $("#mainLoader").css('display','flex')
        // Ajax to validate meter
        $.ajax({
            url:"/validate-bet-wallet/",
            type:"GET",
            data:{
                'accountId':accountId,
                'selectedOperator':selectedOperator,
                // 'meterType':meterType,
                'amount':amount,
            },
            success:function(response){
                console.log(response)
                if(response.code == "00"){
                    $(".discoOperator").html(selectedOperatorName);
                    $(".recipientMeterNum").html(accountId);
                    customerName = response.customerName
                    $(".recipientMeterName").html(customerName);
                    otherData = response.otherField
                    // Format Address                     
                    // let addressData = (response.address).split('Address:')
                    // $(".recipientMeterAddress").html(addressData[1]);
                    $(".billAmount").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    
                    // TODO calculate discount
                    $("#total").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    $("#mainLoader").css('display','none')
                    $("#billSummary").css("display",'block');                    
                }
                else if(response.code == '09'){
                    $(".error-message").html(response.message);
                    $(".error-feedback").css('display','block');
                    $("#buyElectricity").attr('disabled',false);
                    $("#buyElectricity").addClass('disabled');
                    $("#mainLoader").css('display','none')
                };
            }
        })
    })

    // Confirm Pay
    $("#fundBetWallet").on("click",function(){
        $(".error-feedback").css('display','none');
        let button = $(this)
        button.attr('disabled',true);        
        // getTransactionPin()
        fundBetWallet()
    })

    // Cancel Transaction
    $(".cancelTrans").on('click',function(){
        $(".error-feedback").css('display','none');
        $("#buyElectricity").attr('disabled',false);
        $("#buyElectricity").addClass('disabled');
        $("#billSummary").fadeOut();
    });

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target.id == "PINValidation" || event.target.id == 'closePINValidation' || event.target.id == 'transactionFeedback' || event.target.id == 'billSummary') {
            // $("#PINValidation").css("display","none");
            // $(".setting-modal").css("display","none");
            
        }
        else if(event.target.id == "beneficiaryModal"){
            $("#beneficiaryModal").css('display','none');
        }
    };

    // Input field validation
    function inputValid(){
        console.log("Validation Called")
        if( selectedOperator != "" ){
            // console.log(selectedOperator)
            if(accountId != '' && amount >= 100 ){
                $("#fundBetting").attr('disabled',false);
                $("#fundBetting").removeClass('disabled');
                return true;
                
            }
            else{
                $("#fundBetting").attr('disabled',true);
                $("#fundBetting").addClass('disabled');
                return false;
            }
        }
        else{
            $("#fundBetting").attr('disabled',true);
            $("#fundBetting").addClass('disabled');
            return false    ;        
        }
        
    };

    function fundBetWallet(){   
        // $("#PINValidationError").html('')
        // $("#PINValidationError").css('display','none');     
        $("#mainLoader").css('display','flex');
        $.ajax({
            url:'/fund-bet-wallet/',
            type:'POST',
            headers: {'X-CSRFToken': $crf_token},
            data:{
                "accountId":accountId,
                "selectedOperator":selectedOperator,
                "selectedOperatorName":selectedOperatorName,                
                "customerName":customerName,
                "otherField":otherData,
                "amount":amount,
                "saveBeneficiary":saveBeneficiary
            },
            success:function(response){
                console.log(response)
                if( response.code == '00' ){  
                    // $("#PINValidation").css("display","none"); 
                    // Populate Feedback data  
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

})