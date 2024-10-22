$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var amount = 500.00
    var dynamicAccID
    // One time top up
    $("#oneTimeBTN").on('click',function(){
        $("#oneTimeTopup").css("display","block");
    })
    // Amount
    $("#amount").bind("keyup focusout",function(){
        let amount = Number($(this).val());        
        if(!isNaN(amount) && amount >= 100){
            $("#proceedOneTime").removeClass("disabled");
            $("#proceedOneTime").attr("disabled",false);
        }
        else{
            $("#proceedOneTime").attr("disabled",true);
            $("#proceedOneTime").addClass("disabled");            
        }
    })

    // Submit Amount
    $("#proceedOneTime").on('click',function(e){
        e.preventDefault()
        let button = $(this);
        button.attr('disabled',true);
        button.addClass('disabled');
        amount = $("#amount").val()
        $(".loader-overlay").css("display","flex")
        // Ajax
        $.ajax({
            url:"/onetime-topup/",
            type:"POST",
            headers: {'X-CSRFToken': $crf_token},
            data:{
                "amount":amount
            },
            success:function(response){
                console.log(response)
                if(response.code == '00'){
                    $("#topUpAmount").fadeOut(function(){
                        dynamicAccID = response.accountID;
                        let creditAmount = response.creditAmount
                        $("#depositAmount").html(`&#8358;${Number(amount).toLocaleString()}`)
                        $("#creditAmount").html(Number(creditAmount).toFixed(2));
                        $("#oneTimeAccNo").html(response.accountNumber);
                        $("#oneTimeAccountDetails").css('display','block');
                        topUpStatus()
                    })
                }
                $(".loader-overlay").fadeOut()
            },            
        })
    })

    // Confirm Payent
    $("#confirmTopUp").on('click',function(){
        $("#oneTimeAccountDetails").fadeOut(function(){
            // $("#oneTimeAccountDetails").css('display','block');
            $("#oneTimeTopupConfirmation").css('display','block');
            countdown( "ten-countdown", 10, 0 );
        })
    })

    // Copy one Time/Dynamic account number
    $('#copyOneTimeAcc').click(function(e){
        e.preventDefault()
        // alert('COPY CLICKED')
        var copyBTN = $(this);
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('#oneTimeAccNo').text()).select();
        document.execCommand("copy");
        $temp.remove();
        $(copyBTN).css('display','none');
        $('#oneTimeCopyIndicator').css('display','block');
        setTimeout(function(){
          $('#oneTimeCopyIndicator').css('display','none');
          $(copyBTN).css('display','block');
        },1500);
      });


    //   VIRTUAL ACCOUNT SECTION
    $("#virtualAccBTN").on("click",function(){
        $("#virtuaAccModal").css("display","block");
    })

    $(".vacc-nav").on("click",function(){
        $(".vacc-nav").removeClass("active")
        $(this).addClass("active")
    })

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target.id == "oneTimeTopup" || event.target.id == 'closeOneTimeTopup') {
            $("#oneTimeTopup").css("display","none");
            $("#amount").val('');
            $("#oneTimeAccountDetails").css('display','none');
            $("#oneTimeTopupConfirmation").css('display','none');
            $("#oneTimeTopupSuccess").css('display','none');
            $("#topUpAmount").css('display','block');
        }
        else if (event.target.id == "virtuaAccModal" || event.target.id == 'closeVirtuaAccModal') {
            $("#virtuaAccModal").css("display","none");
            // $("#amount").val('');
        };
    }; 

    // One Time account countdown
    function countdown( elementName, minutes, seconds )
        {
            var element, endTime, hours, mins, msLeft, time;

            function twoDigits( n )
            {
                return (n <= 9 ? "0" + n : n);
            }

            function updateTimer()
            {
                msLeft = endTime - (+new Date);
                if ( msLeft < 1000 ) {
                    $('.waiting').fadeOut(function(){
                        $('.payment-pending').css('display','block')
                    })
                } else {
                    time = new Date( msLeft );
                    hours = time.getUTCHours();
                    mins = time.getUTCMinutes();
                    element.innerHTML = (hours ? hours + ':' + twoDigits( mins ) : mins) + ':' + twoDigits( time.getUTCSeconds() );
                    setTimeout( updateTimer, time.getUTCMilliseconds() + 500 );
                }
            }

            element = document.getElementById( elementName );
            endTime = (+new Date) + 1000 * (60*minutes + seconds) + 500;
            updateTimer();
        }

        // countdown( "ten-countdown", 10, 0 );

    // Get Payment status
    function topUpStatus(){
        setInterval(function(){
            $.ajax({
                url:'/transaction-status/',
                type:'GET',
                data:{
                    'accountID':dynamicAccID
                },
                success:function(response){
                    console.log(response)
                    if( response.transactionStatus == 'Completed'){
                        $("#pointsAdded").html(Number(response.settledAmount).toFixed(2))
                        $("#oneTimeAccountDetails").css('display','none');
                        $("#oneTimeTopupConfirmation").css('display','none');
                        $("#oneTimeTopupSuccess").css('display','block');
                        // $("#oneTimeAccountDetails").fadeOut(function(){                            
                        //     $("#oneTimeTopupSuccess").css('display','block');
                        // })
                        // $("#oneTimeTopupConfirmation").fadeOut(function(){                            
                        //     $("#oneTimeTopupSuccess").css('display','block');
                        // })
                        
                    }
                }
            })
        },10000)
    }
});