$(document).ready(function(){
    var usernameError = true
    var emailError = true
    var phoneNumberError = false
    var passwordError = true


    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    // Toggle Password field
    $('.password-reveal').on('click',function(){
        if ($('.passwordInput').attr('type') == 'password'){
            $('.passwordInput').attr('type','text') 
        }
        else{
            $('.passwordInput').attr('type','password') 
        }
    });

    // Username
    $("#username").bind("focusout",function(){
        let username = $(this).val()
        if(username.indexOf(' ') >= 0){
            $("#usernameValidation").empty();
            $("#usernameValidation").append(`<p style="margin-bottom:3px;">username cannot contain spaces</p>`);
            $("#usernameValidation").css('display','block');
        }
        else{
            $.ajax(({
                url:"/validate-username/",
                type:"GET",
                data:{
                    "username":username
                },
                success:function(response){
                    data = response
                    console.log(data)
                    if(data["status"] == "success" && data["message"] == "Invalid"){
                        $("#usernameValidation").empty();
                        $("#usernameValidation").append(`<p style="margin-bottom:3px;">username already exist</p>`);
                        $("#usernameValidation").css('display','block');
                        // usernameError = true
                        // setTimeout(function(){
                        //     $("#username-error").css('display','none')
                        // },2000)
                    }
                    else if (data["status"] == "success" && data["message"] == "Valid"){
                        $("#usernameValidation").css('display','none') ;
                        inputValid();
                    }
                }
            }))



            
        };
        
    });

    // Email
    $("#email").bind("focusout",function(){
        let email = $(this).val()
        if(email.indexOf('@') == -1){
            let feedback = $("#emailValidation").find('p')[0];
            $("#emailValidation").empty();
            $("#emailValidation").append(`<p style="margin-bottom:3px;">please enter a valid email</p>`);
            $("#emailValidation").css('display','block');
        }
        else{

            $.ajax(({
                url:"/validate-email/",
                type:"GET",
                data:{
                    "email":$(this).val()
                },
                success:function(response){
                    data = response
                    if(data["status"] == "success" && data["message"] == "Invalid"){
                        $("#emailValidation").empty();
                        $("#emailValidation").append(`<p style="margin-bottom:3px;">user with email already exist</p>`);
                        $("#emailValidation").css('display','block');
                    }
                    else{
                        $("#emailValidation").css('display','none') ;
                        inputValid();
                    }
                }
            }))
            
        };
        
    });

    // PhoneNumber
    $("#phone_number").bind("focusout",function(){
        $.ajax(({
            url:"/validate-phoneNumber/",
            type:"GET",
            data:{
                "phoneNumber":$(this).val()
            },
            success:function(response){
                data = response
                if(data["status"] == "success" && data["message"] == "Invalid"){
                    $("#phoneValidation").empty();
                    $("#phoneValidation").append(`<p style="margin-bottom:3px;">user with phone number already exist</p>`);
                    $("#phoneValidation").css('display','block');
                    
                }
                else{
                    $("#phoneValidation").css('display','none') ;
                    inputValid();  
                }
            }
        }))
              
    });

    // PhoneNumber
    $("#password").bind("focusout",function(){
        inputValid();        
    });

    $("#createAccountBTN").on('click',function(e){
        e.preventDefault();
        $(".loader-overlay").css('display','flex');
        let form = $('#signup-form'),
        fd = new FormData(form.get(0))

        $.ajax({
            url:'/signup/',
            type: form.attr('method'),
            // contentType: 'multipart/form-data', 
            contentType: false,                   
            dataType: 'json',
            data: fd,
            headers: {'X-CSRFToken': $crf_token},
            processData: false,
            success:function(response){
                if(response.code == '00'){
                    window.location.href = `/confirmation-sent/${response.confirmationID}`
                }
                else if(response.code == '09'){
                    let registrationError = response.registrationError;
                    $.each(registrationError,function(idx,obj){
                        $.each(obj, function(key, value){
                            let valueData = value.split('.')
                            if(key == 'passwordError'){
                                $("#passwordValidation").empty();
                                $.each(valueData,function(i,message){
                                    $("#passwordValidation").append(`<p style="margin-bottom:3px;">${message}</p>`);
                                })
                                $("#passwordValidation").css('display','block');
                            }
                            if(key == 'usernameError'){
                                $("#usernameValidation").empty();
                                $.each(valueData,function(i,message){
                                    $("#usernameValidation").append(`<p style="margin-bottom:3px;">${message}</p>`);
                                });
                                $("#usernameValidation").css('display','block');
                            }
                            if(key == 'emailError'){
                                $("#emailValidation").empty();
                                $.each(valueData,function(i,message){
                                    $("#emailValidation").append(`<p style="margin-bottom:3px;">${message}</p>`);
                                });
                                $("#emailValidation").css('display','block');
                            }
                            if(key == 'phoneError'){
                                $("#phoneValidation").empty();
                                $.each(valueData,function(i,message){
                                    $("#phoneValidation").append(`<p style="margin-bottom:3px;">${message}</p>`);
                                });
                                $("#phoneValidation").css('display','block');
                            }
                        });
                    });
                    $(".loader-overlay").fadeOut();
                    // $(".loader-overlay").css('display','flex');                    
                }
            }

        });
        
    });


    function inputValid(){
        let username = $("#username").val();
        let email = $("#email").val();
        let phone = $("#phone_number").val();
        let password = $("#password").val();

        if(username.indexOf(' ') >= 0){
            let feedback = $("#usernameValidation").find('p')[0];
            $(feedback).html('username cannot contain spaces');
            $("#usernameValidation").css('display','block');
            $("#createAccountBTN").addClass('disabled');
            $("#createAccountBTN").attr('disabled',true);
            return false
        }
        else if( email == '' || phone == '' || password == ''){
            $("#createAccountBTN").addClass('disabled');
            $("#createAccountBTN").attr('disabled',true);
        }
        else{
            $("#createAccountBTN").removeClass('disabled');
            $("#createAccountBTN").attr('disabled',false);
            return true;
        };
    }

    
});