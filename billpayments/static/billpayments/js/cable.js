$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var iconBox;
    var operatorImg;
    var selectedOperator = '';
    var selectedOperatorName;
    var selectedOperatorImg
    var operatorName;
    var customerName 
    var packageId = ''
    var packageName = ''
    var amount = 0;
    var smartcardNumber = '';
    var otherData;
    var bouquetList
    var saveBeneficiary = "off";
    var cableBackend
    var cableDiscount = Number($("#cableDiscount").val())
    // Operator Selector
    $("#operator-selector").on('click',function(){
        // $("#network-dropdown").css("display","block");
        $("#operator-dropdown").fadeIn();
        iconBox = $(this).find('#selectedOperatorImg')[0];
        operatorImg = $(this).find('img')[0];
        operatorName = $(this).find('p')[0];
    })
    // Select Operator
    $(".cable-company").on('click',function(){
        selectedOperator = $(this).attr('network-data');
        selectedOperatorImg = $(this).attr('image-data');
        selectedOperatorName = $(this).attr('disco')
        $(".operator-text").html(selectedOperatorName);
        $(operatorImg).attr('src',selectedOperatorImg);
        $("#selectedOperatorImg").css('display','block');
        $("#operator-dropdown").fadeOut();
        
        //Ajax call to fetch cable bouquet 
        $("#mainLoader").css('display','flex')
        $.ajax({
            url:"/fetch-cable-bouquet/",
            type:'GET',
            data:{
                "selectedOperator":selectedOperator
            },
            success:function(response){
                $("#mainLoader").css('display','none');
                $(".error-feedback").css('display','none');
                if(response.code == '00'){
                    bouquetList = response.bouquetList
                    console.log(bouquetList)
                    cableBackend = response.cableBackend
                    if(cableBackend == "9Payment"){
                        // Update bouquet list
                        $("#cablePackage").empty();
                        $("#cablePackage").append(
                            '<option value="" disabled selected>Select a bouquet</option>'
                        );
                        $.each(bouquetList,function(idx,obj){
                            console.log(obj['itemName'])
                            $("#cablePackage").append(
                                `<option value="${obj.itemId}">${obj.itemName}</option>`
                            )
                            // $.each(obj,function(key,value){
                            //     $("#cablePackage").append(
                            //         `<option value="${obj.itemId}">${obj.itemName}</option>`
                            //     )
                            // })
                        });
                    }
                    else if(cableBackend == "SafeHaven"){
                        $("#cablePackage").empty();
                        $("#cablePackage").append(
                            '<option value="" disabled selected>Select a bouquet</option>'
                        );
                        $.each(bouquetList,function(key,value){
                            let id = value['bundleCode']
                            bundle = value['name']
                            let packageCost = value['amount']
                            if(bundle != "Top Up"){
                                $('#cablePackage').append(`<option value="${id}">${bundle} - ₦${packageCost.toLocaleString()}</option>`)  
                            }                            
                        })
                    }
                    
                }
                else if(response.code == '09'){
                    $(".error-message").html(response.message);
                    // $(".error-feedback").slideUp()
                    $(".error-feedback").css('display','block');
                }
            }
        })


        inputValid()
    });

    // Meter selected
    $("#cablePackage").on("change",function(){
        packageId = $(this).val()
        packageName = $("#cablePackage option:selected").text()
        // let bouquetNameData = packageName.split('-')[1]
        console.log(`backend ${cableBackend}`)
        
        if(cableBackend == "9Payment"){
            $.each(bouquetList,function(idx,obj){
                $.each(obj,function(key,value){
                    // console.log(`selected operator is ${selectedOperator}`)
                    // console.log(`selected operator is ${selectedOperator}`)
                    if(obj.itemId == packageId){
                        console.log(obj.amount)
                        amount = obj.amount
                        
                    }
                })            
                
            });
        }        
        else if(cableBackend == "SafeHaven"){
            // $.each(bouquetList,function(key,value){
            //     if(value['id']== packageId){
            //         console.log(obj.amount)
            //         amount = value['amount']                      
            //     }
                                           
            // })
            $.each(bouquetList,function(idx,obj){
                if(obj.bundleCode == packageId){
                    console.log(obj)
                    console.log(obj.amount)
                    amount = obj.amount                    
                }
            })
        }
        $("#bouquetCost").val(Number(amount).toLocaleString(undefined,{maximumFractionDigits:2}))
        inputValid()
    })

    // Meter Number
    $("#smartcardNumber").bind('keyup focusout',function(){
        smartcardNumber = $(this).val()        
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
        iconBox = $("#operator-selector").find('#selectedOperatorImg')[0];
        operatorImg = $("#operator-selector").find('img')[0];
        operatorName = $("#operator-selector").find('p')[0];
        $(`a[disco="${beneficiaryData[0]}"]`).trigger('click');
        smartcardNumber = beneficiaryData[1];
        $("#smartcardNumber").val(smartcardNumber);
        $("#beneficiaryModal").css('display','none');
        $("#bouquetCost").val("");
        amount = 0;
    })

    // Buy electricity
    $("#buyCable").on('click',function(e){
        e.preventDefault()
        $("#mainLoader").css('display','flex')
        // Ajax to validate meter
        $.ajax({
            url:"/validate-smartcard/",
            type:"GET",
            data:{
                'smartcardNumber':smartcardNumber,
                'selectedOperator':selectedOperator,
                // 'meterType':meterType,
                'amount':amount,
            },
            success:function(response){
                console.log(response)
                if(response.code == "00"){
                    $(".discoOperator").html(selectedOperatorName);
                    $(".recipientMeterNum").html(smartcardNumber);
                    $(".recipientMeterType").html(packageName);
                    customerName = response.customerName
                    $(".recipientMeterName").html(customerName);
                    otherData = response.otherField
                    // Format Address                     
                    // let addressData = (response.address).split('Address:')
                    // $(".recipientMeterAddress").html(addressData[1]);
                    $("#billAmount").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    
                    // TODO calculate discount
                    console.log(`amount is ${amount}`)
                    console.log(`amount is ${amount}`)
                    let calculatedDiscount = (Number(response.amount) * cableDiscount) / 100.00
                    $("#cashback").html(Number(calculatedDiscount).toLocaleString(undefined,{maximumFractionDigits:2,minimumFractionDigits:2}));
                    $("#total").html(Number(amount - calculatedDiscount).toLocaleString(undefined,{maximumFractionDigits:2,minimumFractionDigits:2}));
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
    $("#purchaseCable").on("click",function(){
        $(".error-feedback").css('display','none');
        let button = $(this)
        button.attr('disabled',true);        
        // getTransactionPin()
        buyCable()
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
        // let smartcardNumber = $("#smartcardNumber").val();
        if( selectedOperator != "" ){
            // console.log(selectedOperator)
            if(smartcardNumber != '' && amount != 0 ){
                $("#buyCable").attr('disabled',false);
                $("#buyCable").removeClass('disabled');
                return true;
                
            }
            else{
                $("#buyCable").attr('disabled',true);
                $("#buyCable").addClass('disabled');
                return false;
            }
        }
        else{
            $("#buyCable").attr('disabled',true);
            $("#buyCable").addClass('disabled');
            return false    ;        
        }
        
    };

    function buyCable(){   
        // $("#PINValidationError").html('')
        // $("#PINValidationError").css('display','none');     
        $("#mainLoader").css('display','flex');
        $.ajax({
            url:'/pay-cable-subscription/',
            type:'POST',
            headers: {'X-CSRFToken': $crf_token},
            data:{
                "smartcardNumber":smartcardNumber,
                "selectedOperator":selectedOperator,
                "selectedOperatorName":selectedOperatorName,
                "packageName":packageName,
                "itemId":packageId,
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