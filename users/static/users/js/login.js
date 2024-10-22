$(document).ready(function(){
    $('.password-reveal').on('click',function(){
        if ($('.passwordInput').attr('type') == 'password'){
            $('.passwordInput').attr('type','text') 
        }
        else{
            $('.passwordInput').attr('type','password') 
        }
    });

    // Login Button Clicked
    $("#loginBTN").on("click",function(){
        $(".loader-overlay").css('display','flex');
    })
});