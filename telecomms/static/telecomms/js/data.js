$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var iconBox;
    var operatorImg;
    var selectedOperator;
    var operatorName;
    var planID;
    var planName;
    var price
    var is_ported = "off"
    var safeBeneficiary = "off";

    // Offer Data
    var offerStatus = "None"
    var offerType = ''
    var dataCost
    var offerDiscount

    // Network operator validator
    var AirtelInitials = ['0911','0912','0907','0904','0902','0901','0812','0808','0802','0708','0701']
    var MTNInitials = ['0916','0913','0906','0903','0816','0814','0813','0810','0806','0803','0706','0704','0703','0702','0702']
    var GLOInitials = ['0915','0905','0815','0811','0807','0805','0705']
    var N9MobileInitials = ['0908','0909','0818','0817','0809']

    // IOS/Android Offer
    function androidOrIOS() {
        const userAgent = navigator.userAgent;
        if(/android/i.test(userAgent)){
            return 'android';
        }
        if(/iPad|iPhone|iPod/i.test(userAgent)){
            return 'ios';
        }
    }

    var os = androidOrIOS()


    // network selector
    $("#network-selector").on('click',function(){
        // $("#network-dropdown").css("display","block");
        $("#network-dropdown").fadeIn();
        iconBox = $(this).find('#selectedOperatorImg')[0];
        operatorImg = $(this).find('img')[0];
        operatorName = $(this).find('p')[0];
    })
    // Select Operator
    $(".mobile-operator").on('click',function(){
        // $("#amount").text('');
        $('#error-message').text(``)
        $('.error-feedback').css('display','none')
        selectedOperator = $(this).attr('network-data');
        var selectedOperatorImg = $(this).attr('image-data');
        $(".operator-text").html(selectedOperator);
        $(operatorImg).attr('src',selectedOperatorImg);
        $("#selectedOperatorImg").css('display','block');
        $("#phone_number").val('')
        $("#network-dropdown").fadeOut(function(){
            $(".loader-overlay").css("display","flex");
            // Ajax call to fetch data plans
            $.ajax({
                url:"/fetch-data-plans/",
                type:"GET",
                data:{
                    "operator":selectedOperator
                },
                success:function(response){
                    console.log(response)
                    if(response.code == "00"){
                        $(".error-message").html();
                        $(".error-feedback").css('display','none');
                        let plans = response.plans;
                        $("#dataPlans").empty();
                        // Populate Extra Plans
                        if(response.extraPlans != null && response.activeBackend != "ATN" && selectedOperator == "MTN"){
                            let extraPlans = response.extraPlans;
                            $.each(extraPlans,function(key,value){
                                let planID = value.package_id;
                                let package = value.plan;
                                let price = value.price;
                                let validity = value.validity;                            
                                $("#dataPlans").append(
                                    `<option value='${planID}'>${package}|${validity}|₦${Number(price).toLocaleString()}</option>`
                                );
                            });
                        }
                        $.each(plans,function(key,value){
                            let planID = value.package_id;
                            let package = value.plan;
                            let price = value.price;
                            let validity = value.validity;                            
                            $("#dataPlans").append(
                                `<option value='${planID}'>${package}|${validity}|₦${Number(price).toLocaleString()}</option>`
                            );
                        });
                    }
                    else if(response.code == "09"){
                        $("#dataPlans").empty();
                        $("#dataPlans").append(
                            `<option value='' selected disabled>Unavailable</option>`
                        );
                        $(".error-message").html(response.message);
                        // $(".error-feedback").slideUp()
                        $(".error-feedback").css('display','block');
                    };
                    $(".loader-overlay").fadeOut();
                }
            })
        });

        // Set Operator discount
        // $.each(discountData,function(key,value){
        //     if(value.networkOperator == selectedOperator){
        //         discountRate = Number(value.rate)
        //         console.log(discountRate);
        //     };
            
        // });

        
    });

    // Open Saved Beneficiary
    $("#safeBeneficiary").on("click",function(){
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
        inputValid()
    })

    // Beneficiary Modal
    $(".open-beneficiary").on('click',function(){
        $("#beneficiaryModal").css('display','block')
    })


    // Data plans selected
    $("#dataPlans").on('change',function(){
        planID = $(this).val();        
        inputValid()
        // let planData = planID.split("|");
        // price = Number(planData[3]).toLocaleString()
        // console.log(`data price is ${price}`)
        // let planPrice = 
        // $("#amount").text(`VP${Number(planData).toLocaleString}`);
    });

    // Phone Number Input Logic
    $("#phone_number").bind('focusout keyup',function(){
        if (inputValid()){
            $("#buyData").removeClass('disabled');
        }
        else{
            $("#buyData").addClass('disabled');
            $("#buyData").attr('disabled',true);
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

    // Proceed to buy
    $("#buyData").on('click',function(e){
        e.preventDefault();
        if(recipientValid() || (!recipientValid() && is_ported == "on")){
            $('#error-message').text(``)
            $('.error-feedback').css('display','none')
            let button  = $(this)
            button.attr('disabled',true);
            button.addClass('disabled')
            let planDatails = $("#dataPlans option:selected").text().split('|');
            let priceData = planDatails[3].split('₦');
            dataCost = priceData[1]
            // console.log(`price data ${planDatails}`);
            price = Number(priceData[1]).toLocaleString(undefined, {minimumFractionDigits: 2});
            recipient = $("#phone_number").val();
            planID = $("#dataPlans").val();
            planName = `${planDatails[0]}|${planDatails[1]} for ${planDatails[2]}`  

            // TODO Evaluate Billsummary

            $("#networOperator").html(selectedOperator.toUpperCase());
            $("#recipient").html(recipient);
            $("#plan").html(planName);
            $("#dataAmount").html(price);
            $("#cashback").html(5.00);  
            $("#total").html(price);        
            
            
            // Get available offer
            if(os == "android" || os == "ios"){
                $.ajax({
                    url:"/available-offer/",
                    typr:"GET",
                    success:function(response){
                        console.log(response);
                        if(response.code == '00'){
                            offerDiscount = response.discount
                            offerType = response.currentOffer;
                            
                            // Remove
                            button.attr('disabled',false);
                            button.removeClass('disabled')
                            // End Remove
                            if(offerType == 'storeRating'){                            
                                if(os == "android"){
                                    $("#playstoreRating").css('display','block');
                                }
                                else if( os == "ios"){
                                    $("#appstoreRating").css('display','block');
                                }
                            }
                            else if(offerType == 'trustPilot'){                            
                                $("#trustPilotRating").css('display','block');
                            }
                            
                            $(".offer-amount").html((Number(dataCost) - Number(offerDiscount)).toLocaleString());
                            $("#offerModal").css("display","block");
                        }
                        else if(response.code == '04'){
                            $("#billSummary").css("display",'block');
                        }
                    }
                })
            }
            else{
                $("#billSummary").css("display",'block');
            }
            

            

        }
        
    })

    // Accept Offer
    $(".accept-offer").on("click",function(){
        console.log("We enetered here")
        $(".offer-prompt").css("display","none");
        $(".offer-pending").css("display","block");
        setTimeout(function(){
            console.log("countdown started")
            $(".confirm-offer").css("display","block");
        },20000)
    })

    // Confirm Offer
    $(".continue-offer").on("click",function(){
        // $("#dataAmount").html(price);
        $("#cashback").html(offerDiscount);  
        $("#total").html((Number(dataCost) - Number(offerDiscount)).toLocaleString()); 
        offerStatus = "claimed";
        $("#offerModal").css("display","none");
        $("#billSummary").css("display",'block');
    })

    // Reject Offer
    $(".reject-offer").on("click",function(){
        offerStatus = "rejected";
        console.log(offerStatus)
        $("#offerModal").css("display","none");
        $("#billSummary").css("display",'block');
    })

    // Purchase Airtime
    $("#purchaseData").click(function(){
        $(".error-feedback").css('display','none');
        let button = $(this);
        button.attr('disabled',true);
        // getTransactionPin()
        
        buyData()
        
    });

    // Cancel Transaction
    $(".cancelTrans").on('click',function(){
        $(".error-feedback").css('display','none');
        $("#buyData").attr('disabled',false);
        $("#billSummary").fadeOut();
    });


    // Operator Validation
    function recipientValid(){
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
        let planID = $("#dataPlans").val();
        if($(".operator-text").html() != "Select a network"){
            if(phoneNum.length == 11 && planID != "" ){
                $("#buyData").attr('disabled',false);
                return true;
            }
            else{
                $("#buyData").attr('disabled',true);
                return false;
                
            }
        }
        else{
            $("#buyData").attr('disabled',true);
            return false;        
        }
        
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
                buyData(transcationPin=pin)
                  },
            });
          })
    }
    function buyData(){
        $("#PINValidationError").html('')
        $("#PINValidationError").css('display','none');     
        $(".loader-overlay").css('display','flex');
        $.ajax({
            url:'/purchase-data/',
            type:'POST',
            headers: {'X-CSRFToken': $crf_token},
            data:{
                "operator":selectedOperator,
                "recipient":recipient,
                "planID":planID,
                "is_ported":is_ported,
                "offerStatus":offerStatus,
                "offerType":offerType,
                "safeBeneficiary":safeBeneficiary
                // 'transcationPin':transcationPin,
            },
            success:function(response){
                console.log(response)
                if( response.code == '00' ){ 
                    $("#PINValidation").css("display","none");
                    $("#billSummary").fadeOut(function(){
                        $(".loader-overlay").css('display','none');
                        $("#transactionFeedback").css("display",'block');
                    });
                    

                }
                else if(response.code == '01'){
                    // $("#PINValidationError").html(response.message)
                    // $("#PINValidationError").css('display','block');
                    $("#purchaseAirtime").attr('disabled',false);
                }
                else if(response.code == '09'){
                    $(".error-message").html(response.message);
                    // $(".error-feedback").slideUp()
                    $(".error-feedback").css('display','block');
                    $("#purchaseData").attr('disabled',false);
                    // $('#PINValidation').fadeOut()
                };
                $(".loader-overlay").css('display','none');
            }
        });

    }

})