$(document).ready(function(){
    let timerOn = true;
    let resendBtn = $(".otpBTN")

    function timer(remaining) {
    var m = Math.floor(remaining / 60);
    var s = remaining % 60;
    
    //   m = m < 10 ? '0' + m : m;
    s = s < 10 ? '0' + s : s;
    resendBtn.html(`Resend in <span id="timer">${s}</span>s`)
    // document.getElementById('timer').innerHTML = s;
    remaining -= 1;
    
    if(remaining >= 0 && timerOn) {
        setTimeout(function() {
            timer(remaining);
        }, 1000);
        return;
    }

    if(!timerOn) {
        // Do validate stuff here
        // document.getElementById('timer').innerHTML = m + ':' + s;
        return;
    }
    
    // Do timeout stuff here
    timerOn = false;
    resendBtn.addClass('active');
    resendBtn.html('Resend');
    // alert('Timeout for otp');
    }
    // Resend OTP
    $("#resendOTP").on('click',function(){
        if(timerOn){
            return;
        }
        else{
            
            let button = $(this);
            button.removeClass('active');
            // Resend OTP
            $.ajax({
                url:"/resend-registration-code/",
                type:"GET",
                data:{
                    "confirmationID":$("#confirmationID").val(),
                },
                success:function(response){
                    if(response.code == "00"){
                        $(".resend-feedback").css({'display':'flex',});
                        timerOn = true;
                        timer(15);
                    }
                    else if (response.code == "09"){
                        cd 
                    }
                }
            })
            
        };
        
    })

    timer(60);

    // Close OTP
    $(".closeOTPFeedback").on('click',function(){
        $(".resend-feedback").fadeOut();
        $(".resend-feedback").css({'display':'flex',});
        
    });

    // OTP CODDE
    $(function(){
        $('#PINWrapper').pinlogin({
          fields : 6, // default 5
          placeholder:'*', // default: '•'
          reset :false,
          complete :function(pin){
            console.log(pin)
            $("#error-message").html('')
            $("#regOTPError").css("display","none")
            $(".loader-overlay").css('display','flex');
            $.ajax({
                url:"/verify-registration/",
                type:'GET',
                data:{
                    "confirmationID":$("#confirmationID").val(),
                    "otp":pin
                },
                success:function(response){
                    console.log(response)
                    if (response.code == "09"){
                        $("#error-message").html(response.message)
                        $("#regOTPError").css("display","block")
                        $(".loader-overlay").css('display','none');
                    }
                    else if(response.code == "00"){
                        $(".otp-sent-section").fadeOut(function(){
                            $(".registration-successful").css('display',"block")
                        });
                        $(".loader-overlay").css('display','none');
                        setTimeout(function(){
                            window.location.replace("/dashboard/");
                            // window.location.href = "/login/"
                        },10000)
                    }
                    
                }
            })
            
            
            },
        });
      })

    
});

