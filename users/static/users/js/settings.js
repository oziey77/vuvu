$(document).ready(function(){
    // Set bottom nav Icon
    $("#settingsNormal").css('display','none')
    $("#settingsActive").css('display','block')
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    // Change Password
    var newPasswordError = true
    $("#changePassword").on("click",function(){
        $("#changePasswordModal").css("display","block");
    });

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target.id == "changePasswordModal" || event.target.id == 'closePasswordChange') {
            $("#changePasswordModal").css("display","none");
            $("#passwordChangeFeedback").css("display","none");
            $("#passwordForm").trigger('reset');
            $("#passwordChangeForm").css("display","block");
        };
    };    
    //Old password
    $("#oldPassword").bind('keyup focusout',function(){
        $("#oldPasswordValidation").empty();
        $("#oldPasswordValidation").css('display','none');
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

    // Drop
    var acc = document.getElementsByClassName("multilevel-drop");
    var i;

    for (i = 0; i < acc.length; i++) {
    acc[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var panel = this.nextElementSibling;
        if (panel.style.maxHeight) {
        panel.style.maxHeight = null;
        } else {
        panel.style.maxHeight = panel.scrollHeight + "px";
        }
    });
    }

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
            url:'/change-password/',
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
                    let registrationError = response.data
                    console.log(registrationError)
                    $.each(registrationError,function(idx,obj){
                        console.log(obj)
                        console.log(obj.message)
                        $("#oldPasswordValidation").empty();
                        $("#oldPasswordValidation").append(`<p style="margin-bottom:3px;">${obj.message}</p>`);
                        $("#oldPasswordValidation").css('display','block');
                        $("#submitNewPassword").attr("disabled",true);
                        $("#submitNewPassword").addClass("disabled");
                    });
                    $(".loader-overlay").fadeOut();

                }
                else if(response.code == '00'){
                    $("#passwordChangeForm").css("display","none");
                    $("#passwordChangeFeedback").css("display","block");
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
        let oldPassword = $("#oldPassword").val()
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