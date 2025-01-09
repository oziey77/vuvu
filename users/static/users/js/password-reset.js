$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    // Change Password
    var newPasswordError = true
    var confirmID = ""

    // Registered Email
    $("#email").bind("keyup focusout",function(){
        $("#emailValidation").css("display","none");
        let email = $(this).val()
        if(email.indexOf('@') != -1){
            $("#submitEmail").attr("disabled",false);
            $("#submitEmail").removeClass("disabled"); 
        }
        else{
            $("#submitEmail").attr("disabled",true);
            $("#submitEmail").addClass("disabled"); 
        }
    })

    // Submit email
    $("#submitEmail").on('click',function(e){
        e.preventDefault();
        let button = $(this);
        button.attr("disabled",true);
        button.addClass("disabled");
        $(".loader-overlay").css("display","flex");

        // Ajax Call
        $.ajax({
            url:"/send-otp/",
            type:"POST",
            data:{
                "email":$("#email").val(),
            },
            headers: {'X-CSRFToken': $crf_token},
            success:function(response){
                console.log(response);
                if(response.code == "00"){
                    confirmID = response.confirmCode
                    $(".registered-email-section").fadeOut(function(){
                        $("#passwordChangeForm").css("display","block");
                    });
                    $("#confirmationID").val(confirmID)
                    $(".loader-overlay").fadeOut();
                }
                else if(response.code == "09"){
                    $("#emailValidation").css("display","block");
                    $(".loader-overlay").fadeOut();
                }
            }
        });
        
    })

    //Old password
    $("#otp").bind('keyup focusout',function(){
        $("#otpValidation").empty();
        $("#otpValidation").css('display','none');
        inputValid()
    })

    // Password 1
    $("#newPassword1").bind('keyup focusout',function(){
        let password = $(this).val()
        $("#password1Validation").css("display","block")
        if(passwordValid(password)){
            $("#password1Validation").css("display","none")
            newPasswordValid()
            inputValid()
        }
    })
    $("#newPassword2").bind('keyup focusout',function(){
        newPasswordValid()
        inputValid()
    })

    // Toggle Password field
    $('.password-reveal').on('click',function(){
        let btn = $(this)
        let trgt = $(this).attr('data-target')
        if ($(`#${trgt}`).attr('type') == 'password'){
            $(`#${trgt}`).attr('type','text') 
            btn.html('Hide')
        }
        else{
            $(`#${trgt}`).attr('type','password') 
            btn.html('Show')
        }
    });

    // Submit New Password form
    $("#submitNewPassword").on("click",function(e){
        e.preventDefault();
        let button = $(this);
        button.attr("disabled",true);
        button.addClass("disabled");
        $(".loader-overlay").css("display","flex");
        let form = $('#passwordForm');
        fd = new FormData(form.get(0));
        $.ajax({
            url:'/reset-password/',
            type: form.attr('method'),
            // contentType: 'multipart/form-data', 
            contentType: false,                   
            dataType: 'json',
            data: fd,
            headers: {'X-CSRFToken': $crf_token},
            processData: false,
            success:function(response){
                if(response.code == '09'){
                    console.log(response)
                    // let registrationError = response.data
                    // console.log(registrationError)
                    // $("#otpValidation").empty();
                    // $("#otpValidation").append(`<p>${response.data}</p>`);
                    $("#otpValidation").css('display','block');
                    $("#submitNewPassword").attr("disabled",true);
                    $("#submitNewPassword").addClass("disabled");
                    // $.each(registrationError,function(idx,obj){
                    //     console.log(obj)
                    //     console.log(obj.message)
                    //     $("#otpValidation").empty();
                    //     $("#otpValidation").append(`<p>${obj.message}</p>`);
                    //     $("#otpValidation").css('display','block');
                    //     $("#submitNewPassword").attr("disabled",true);
                    //     $("#submitNewPassword").addClass("disabled");
                    // });
                    $(".loader-overlay").fadeOut();

                }
                else if(response.code == '00'){
                    $("#passwordChangeForm").css("display","none");
                    $(".reset-successful").css("display","block");
                    $(".loader-overlay").fadeOut();                    
                }
            }
        })
    })

    // Validate new password
    function passwordValid(value){
        var upperCase= new RegExp('[A-Z]');
        var lowerCase= new RegExp('[a-z]');
        var numbers = new RegExp('[0-9]');

        if(value.match(upperCase) && value.match(lowerCase) && value.match(numbers) && value.length >= 8)  
        {
            return true

        }
        else
        {
            return false
        }
    }


    // confirm new password
    function newPasswordValid(){
        let password1 = $("#newPassword1").val();
        let password2 = $("#newPassword2").val();
        if( password1 != '' && password2 != ''){
            if(password1 != password2 ){
                $("#password2Validation").css("display","block")
                newPasswordError = true
            }
            else{
                $("#password2Validation").css("display","none")
                newPasswordError = false
            }
        }

    }

    // Validate in input
    function inputValid(){
        let oldPassword = $("#otp").val()
        if(newPasswordError == false && oldPassword != ''){            
            $("#submitNewPassword").removeClass("disabled");
            $("#submitNewPassword").attr("disabled",false); 
            
        }
        else{
            $("#submitNewPassword").attr("disabled",true);
            $("#submitNewPassword").addClass("disabled"); 
        }
    }

});