$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var iconBox;
    var operatorImg;
    var selectedOperator;
    var selectedOperatorName;
    var selectedOperatorImg
    var operatorName;
    var customerName 
    var meterType = ''
    var meterTypeText = ''
    var amount;
    var meterNumber;
    var otherData;
    var saveBeneficiary = "off";
    // Operator Selector
    $("#operator-selector").on('click',function(){
        // $("#network-dropdown").css("display","block");
        $("#operator-dropdown").fadeIn();
        iconBox = $(this).find('#selectedOperatorImg')[0];
        operatorImg = $(this).find('img')[0];
        operatorName = $(this).find('p')[0];
    })
    // Select Operator
    $(".disco").on('click',function(){
        selectedOperator = $(this).attr('network-data');
        selectedOperatorImg = $(this).attr('image-data');
        selectedOperatorName = $(this).attr('disco')
        $(".operator-text").html(selectedOperatorName);
        $(operatorImg).attr('src',selectedOperatorImg);
        $("#selectedOperatorImg").css('display','block');
        $("#operator-dropdown").fadeOut();
        inputValid()
    });

    // Meter selected
    $("#meterType").on("change",function(){
        meterType = $(this).val()
        meterTypeText = $("#meterType option:selected").text()
        inputValid()
    })

    // Meter Number
    $("#meterNumber").bind('keyup focusout',function(){
        meterNumber = $(this).val()        
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
    $("#buyElectricity").on('click',function(e){
        e.preventDefault()
        $("#mainLoader").css('display','flex')
        // Ajax to validate meter
        $.ajax({
            url:"/validate-meter/",
            type:"GET",
            data:{
                'meterNumber':meterNumber,
                'selectedOperator':selectedOperator,
                'meterType':meterType,
                'amount':amount,
            },
            success:function(response){
                console.log(response)
                if(response.code == "00"){
                    $(".discoOperator").html(selectedOperatorName);
                    $(".recipientMeterNum").html(meterNumber);
                    $(".recipientMeterType").html(meterTypeText);
                    customerName = response.customerName
                    $(".recipientMeterName").html(customerName);
                    if(response.backend == "9Payment"){
                        otherData = response.address
                        // Format Address                     
                        let addressData = (response.address).split('Address:')
                        $(".recipientMeterAddress").html(addressData[1]);
                    }
                    else if(response.backend == "SafeHaven"){
                        otherData = response.address
                        $(".recipientMeterAddress").html(response.address);
                    }
                    
                    $(".billAmount").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    
                    // TODO calculate discount
                    $("#total").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    $("#mainLoader").css('display','none')
                    $("#billSummary").css("display",'block');   
                    $(".error-feedback").css('display','none');                 
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
    $("#purchaseElectricity").on("click",function(){
        $(".error-feedback").css('display','none');
        let button = $(this)
        button.attr('disabled',true);        
        // getTransactionPin()
        buyElectricity()
    })

    // Cancel Transaction
    $(".cancelTrans").on('click',function(){
        $(".error-feedback").css('display','none');
        $("#buyElectricity").attr('disabled',false);
        $("#buyElectricity").addClass('disabled');
        $("#billSummary").fadeOut();
    });

    // Copy one Serial Number
    $('#copyToken').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('#paymentToken').text()).select();
        document.execCommand("copy");
        $temp.remove();
        // $(copyBTN).css('display','none');
        $('#copyIndicator').css('display','block');
        setTimeout(function(){
          $('#copyIndicator').css('display','none');
          $(copyBTN).css('display','block');
        },1500);
      });

      // Copy one Serial Number
    $('#copyReference').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('#paymentReference').text()).select();
        document.execCommand("copy");
        $temp.remove();
        // $(copyBTN).css('display','none');
        $('#copyIndicator').css('display','block');
        setTimeout(function(){
          $('#copyIndicator').css('display','none');
          $(copyBTN).css('display','block');
        },1500);
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
        let meterNum = $("#meterNumber").val();
        let amount = Number($("#amount").val());
        if( selectedOperator != "Select your electricity company"){
            // console.log(selectedOperator)
            if(meterNum.length >= 0 && amount >= 1000 ){
                $("#buyElectricity").attr('disabled',false);
                $("#buyElectricity").removeClass('disabled');
                return true;
                
            }
            else{
                $("#buyElectricity").attr('disabled',true);
                $("#buyElectricity").addClass('disabled');
                return false;
            }
        }
        else{
            $("#buyElectricity").attr('disabled',true);
            $("#buyElectricity").addClass('disabled');
            return false    ;        
        }
        
    };

    function buyElectricity(){   
        // $("#PINValidationError").html('')
        // $("#PINValidationError").css('display','none');     
        $("#mainLoader").css('display','flex');
        $.ajax({
            url:'/pay-electricity/',
            type:'POST',
            headers: {'X-CSRFToken': $crf_token},
            data:{
                "meterNumber":meterNumber,
                "selectedOperator":selectedOperator,
                "selectedOperatorName":selectedOperatorName,
                "meterType":meterTypeText,
                "itemId":meterType,
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
                    $("#paymentDiscoImage").attr('src',selectedOperatorImg);
                    // Extract token from data
                    if(response.isToken == true){
                        if(response.backend == '9Payment'){
                            if(response.isToken == true){
                                let rawToken = response.token.split('|');
                                let tokenData = rawToken[0].split(':');
                                $("#paymentToken").html(tokenData[1]); 
                                // Extract Units data
                                let rawUnits = response.units.split(':')
                                $("#paymentUnits").html(rawUnits[1]); 
                            }
                            
                        }
                        else if(response.backend == 'SafeHaven'){
                            $("#paymentToken").html(response.token); 
                            $("#paymentUnits").html(response.units); 
                        }
                        $("#paymentReference").html(response.reference); 
                        $("#paymentDate").html(response.date);
                        $("#paymentDisco").html(selectedOperatorName);
                        $("#billSummary").fadeOut(function(){
                            $(".loader-overlay").css('display','none');
                            $("#billsFeedback").css("display",'block');
                        });
                    }
                    else{
                        $("#billSummary").fadeOut(function(){
                            $(".loader-overlay").css('display','none');
                            $("#transactionFeedback").css("display",'block');
                        });
                    }
                    
                    
                    
                    
                    

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