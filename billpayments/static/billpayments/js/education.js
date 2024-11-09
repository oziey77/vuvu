$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var iconBox;
    var operatorImg;
    var selectedOperator = '';
    var selectedOperatorName;
    var selectedOperatorImg
    var operatorName;
    var customerName = '';
    var packageId = ''
    var packageName = ''
    var amount = 0;
    // var customerID = '';
    var otherData;
    var bouquetList
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
    $(".exam-body").on('click',function(){
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
            url:"/fetch-education-data/",
            type:'GET',
            data:{
                "selectedOperator":selectedOperator
            },
            success:function(response){
                $("#mainLoader").css('display','none');
                if(response.code == '00'){
                    bouquetList = response.bouquetList
                    console.log(bouquetList)
                    // Update bouquet list
                    $("#examData").empty();
                    $("#examData").append(
                        '<option value="" disabled selected>Select exam</option>'
                    );
                    $.each(bouquetList,function(idx,obj){
                        console.log(obj['itemName'])
                        $("#examData").append(
                            `<option value="${obj.itemId}">${obj.itemName}</option>`
                        )
                        // $.each(obj,function(key,value){
                        //     $("#cablePackage").append(
                        //         `<option value="${obj.itemId}">${obj.itemName}</option>`
                        //     )
                        // })
                    });
                }
            }
        })


        // inputValid()
    });

    // Meter selected
    $("#examData").on("change",function(){
        packageId = $(this).val()
        // packageName = $("#examData option:selected").text()
        // alert(packageName)
        // let bouquetNameData = packageName.split('-')[1]
        
        $.each(bouquetList,function(idx,obj){
            $.each(obj,function(key,value){
                // console.log(`selected operator is ${selectedOperator}`)
                // console.log(`selected operator is ${selectedOperator}`)
                if(obj.itemId == packageId){
                    console.log(obj.amount)
                    amount = obj.amount
                    packageName = obj.itemName.split("-")[0]
                    console.log(`Packege name is ${packageName}`)
                    
                }
            })
        });
        $("#bouquetCost").val(Number(amount).toLocaleString(undefined,{maximumFractionDigits:2}))
        
        inputValid()
    })

    // Meter Number
    $("#customerName").bind('keyup focusout',function(){
        customerName = $(this).val()        
        inputValid()
    })

   

    // Buy Internet click
    $("#payExam").on('click',function(e){
        e.preventDefault()
        $("#mainLoader").css('display','flex')

        $(".discoOperator").html(selectedOperatorName);
        // $(".recipientMeterNum").html(customerID);
        $(".PINType").html(packageName);
        // customerName = response.customerName
        $(".recipientMeterName").html(customerName);
        $(".billAmount").html(Number(amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    
        // TODO calculate discount
        $("#total").html(Number(amount).toLocaleString(undefined,{maximumFractionDigits:2}));
        $("#mainLoader").css('display','none')
        $("#billSummary").css("display",'block');  
        // Ajax to validate meter
        // $.ajax({
        //     url:"/validate-isp-customer/",
        //     type:"GET",
        //     data:{
        //         'customerID':customerID,
        //         'selectedOperator':selectedOperator,
        //         // 'meterType':meterType,
        //         'amount':amount,
        //     },
        //     success:function(response){
        //         console.log(response)
        //         if(response.code == "00"){
        //             $(".discoOperator").html(selectedOperatorName);
        //             $(".recipientMeterNum").html(customerID);
        //             $(".recipientMeterType").html(packageName);
        //             customerName = response.customerName
        //             $(".recipientMeterName").html(customerName);
        //             otherData = response.otherField
        //             // Format Address                     
        //             // let addressData = (response.address).split('Address:')
        //             // $(".recipientMeterAddress").html(addressData[1]);
        //             $(".billAmount").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
                    
        //             // TODO calculate discount
        //             $("#total").html(Number(response.amount).toLocaleString(undefined,{maximumFractionDigits:2}));
        //             $("#mainLoader").css('display','none')
        //             $("#billSummary").css("display",'block');                    
        //         }
        //         else if(response.code == '09'){
        //             $(".error-message").html(response.message);
        //             $(".error-feedback").css('display','block');
        //             $("#buyElectricity").attr('disabled',false);
        //             $("#buyElectricity").addClass('disabled');
        //             $("#mainLoader").css('display','none')
        //         };
        //     }
        // })
    })

    // Confirm Pay
    $("#purchaseEPin").on("click",function(){
        $(".error-feedback").css('display','none');
        let button = $(this)
        button.attr('disabled',true);        
        // getTransactionPin()
        payExam()
    })

    // Cancel Transaction
    $(".cancelTrans").on('click',function(){
        $(".error-feedback").css('display','none');
        $("#buyElectricity").attr('disabled',false);
        $("#buyElectricity").addClass('disabled');
        $("#billSummary").fadeOut();
    });

    // Copy one Serial Number
    $('#copySerialNum').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('#serialNum').text()).select();
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
    $('#copyExamPIN').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('#examPIN').text()).select();
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
        // let smartcardNumber = $("#smartcardNumber").val();
        if( selectedOperator != "" ){
            // console.log(selectedOperator)
            if(customerName != '' && amount != 0 ){
                $("#payExam").attr('disabled',false);
                $("#payExam").removeClass('disabled');
                return true;
                
            }
            else{
                $("#payExam").attr('disabled',true);
                $("#payExam").addClass('disabled');
                return false;
            }
        }
        else{
            $("#payExam").attr('disabled',true);
            $("#payExam").addClass('disabled');
            return false    ;        
        }
        
    };

    function payExam(){   
        // $("#PINValidationError").html('')
        // $("#PINValidationError").css('display','none');     
        $("#mainLoader").css('display','flex');
        $.ajax({
            url:'/buy-education-pin/',
            type:'POST',
            headers: {'X-CSRFToken': $crf_token},
            data:{
                // "customerID":customerID,
                "selectedOperator":selectedOperator,
                "selectedOperatorName":selectedOperatorName,
                "packageName":packageName,
                "itemId":packageId,
                "customerName":customerName,
                "otherField":otherData,
                "amount":amount,
                // "saveBeneficiary":saveBeneficiary
            },
            success:function(response){
                console.log(response)
                if( response.code == '00' ){  
                    // $("#PINValidation").css("display","none"); 
                    // Populate Feedback data  
                    let data = response.data
                    let serialNo = data['otherField'].split(':')[1]
                    let examPin = data['token'].split(':')[1]
                    $("#serialNum").html(serialNo)
                    $("#examPIN").html(examPin)

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