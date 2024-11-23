$(document).ready(function(){
    // Set bottom nav Icon
    $("#transactionsNormal").css('display','none')
    $("#transactionsActive").css('display','block')
    let currentFilter = $("#currentFilter").val();
    if(currentFilter != ''){
        $('#filterBy').val(currentFilter).change();
    }
    // Filter changed
    $("#filterBy").on('change',function(){
        $("#transactionFilterForm").submit();
    });

    // Get transaction details
    $(".transInfo").on('click',function(){
        let transID = $(this).attr('transID');
        let operatorImg = $(this).find('img')[0];
        $(".loader-overlay").css('display','flex')
        $.ajax({
            url:`/trasnsaction-detail/${transID}`,
            type:"GET",
            success:function(response){
                console.log(response)
                if(response.code == '00'){
                    let data = response.data;
                    // update transaction Info   
                    if(data.transaction_type == 'Airtime' || data.transaction_type == 'Data'){
                        $('.transaction-type').html(data.transaction_type);
                        $('#operator').html(data.operator);
                        $('#recipient').html(data.recipient);
                        $('#transAmount').html(data.unit_cost);
                        $('#cashback').html(data.discount);
                        $('#status').html(data.status);
                        $('#date').html(data.created);
                        $('.telTransRef').html(data.reference);
                        // $('#supportDefault').attr('href',`https://wa.me/2349063942497?text=Hello%2CI+have+an+issue+with+this+Airtime+Purchase%3A${data.reference}`)
                        $('.supportDefault').attr('href',`https://wa.me/2349166466849?text=Hello%2C+I+have+an+issue+with+this+Airtime+Purchase%3A+${data.reference}`)
                        if(data.transaction_type == 'Data'){
                            $('#package').html(data.package); 
                            $('#dataPackage').css('display','flex') 
                            $('.supportDefault').attr('href',`https://wa.me/2349166466849?text=Hello%2C+I+have+an+issue+with+this+Data+Purchase%3A+${data.reference}`)                          
                        }
                        $("#operatorImg").attr('src',$(operatorImg).attr('src'));
                        $("#cableDetails").css('display','none');
                        $("#airtimeDetails").css('display','block');
                        // $(".loader-overlay").css('display','none')
                        $(".loader-overlay").fadeOut(function(){
                            $("#transaction-details-container").css('display','block');
                        });
                    }
                    else if(data.transaction_type == 'Electricity'){
                        $("#paymentDiscoImage").attr('src',$(operatorImg).attr('src'));
                        $('#paymentAmount').html(Number(data.unit_cost).toLocaleString());
                        $('#paymentToken').html(data.token)
                        $('#paymentReference').html(data.reference)
                        $('#paymentUnits').html(data.electricity_units)
                        $('#recipientMeterNum').html(data.recipient)
                        $('#recipientMeterType').html(data.package)
                        $('#recipientMeterName').html(data.customerName)
                        $('#recipientMeterAddress').html(data.customerAddress)
                        $('#paymentDate').html(data.created)
                        $('.transStatus').html(data.status)
                        $('.supportDefault').attr('href',`https://wa.me/2349166466849?text=Hello%2C+I+have+an+issue+with+this+Data+Electricity%3A+${data.reference}`)
                        $(".loader-overlay").fadeOut(function(){
                            $("#billsFeedback").css('display','block');
                        });
                    }
                    else if(data.transaction_type == 'Cable'){
                        $('.transaction-type').html(data.transaction_type);
                        $('#cableOperator').html(data.operator);
                        $('#smartcardNo').html(data.recipient);
                        $('#cablePackage').html(data.package); 
                        $('#cableTransAmount').html(Number(data.unit_cost).toLocaleString());
                        $('.cashback').html(data.discount);
                        $('#cableTranStatus').html(data.status);
                        $('#cableTransDate').html(data.created);
                        $('.cableTransRef').html(data.reference);
                        
                        // $('#supportDefault').attr('href',`https://wa.me/2349063942497?text=Hello%2CI+have+an+issue+with+this+Airtime+Purchase%3A${data.reference}`)
                        $('.supportDefault').attr('href',`https://wa.me/2349166466849?text=Hello%2C+I+have+an+issue+with+this+Airtime+Purchase%3A+${data.reference}`)                        
                        $("#cableOperatorImg").attr('src',$(operatorImg).attr('src'));
                        $("#airtimeDetails").css('display','none');
                        $("#cableDetails").css('display','block');
                        // $(".loader-overlay").css('display','none')
                        $(".loader-overlay").fadeOut(function(){
                            $("#transaction-details-container").css('display','block');
                        });
                    }
                    
                };
            }
        });
        
    });

    // Close Transaction details
    $("#closeTransDetail").on('click',function(){        
        $("#transaction-details-container").fadeOut();
        $('#package').html(''); 
        $('#dataPackage').css('display','none') 
    });

    // Copy Reference
    $('.copyTelReference').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('.telTransRef').text()).select();
        document.execCommand("copy");
        $temp.remove();
        $(copyBTN).css('display','none');
        $('.refCopyIndicator').css('display','block');
        setTimeout(function(){
          $('.refCopyIndicator').css('display','none');
          $(copyBTN).css('display','block');
        },1500);
      });

    // Copy cable Reference
    $('.copyCableReference').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('.cableTransRef').text()).select();
        document.execCommand("copy");
        $temp.remove();
        $(copyBTN).css('display','none');
        $('.refCopyIndicator').css('display','block');
        setTimeout(function(){
          $('.refCopyIndicator').css('display','none');
          $(copyBTN).css('display','block');
        },1500);
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
        if (event.target.id == "transaction-details-container" || event.target.id == "billsFeedback" ) {
            // $("#PINValidation").css("display","none");
            $(".setting-modal").css("display","none");
            
        };
    };


});