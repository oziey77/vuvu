$(document).ready(function(){
    // Set bottom nav Icon
    $("#storiesNormal").css('display','none')
    $("#storiesActive").css('display','block')
    // alert("we connected")
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');

    // Attach Files
    $("#selectFiles").on("click",function(){
        $("#attachFilles").click()
    })

    // Number of Files
    $("input[type='file']").on("change", function(){  
        var numFiles = $(this).get(0).files.length;
        if(numFiles > 0){
            $("#filesCount").html(numFiles)
            $(".filesFeedback").css('display','block')
        }
        else{
            $(".filesFeedback").css('display','none') 
        }
    });

    setTimeout(function(){
        $(".feedback-message").css("display","none")
    },2000)

    // 
    $(".input-method").on("click",function(){
        $(".input-method").removeClass("active")
        $(this).addClass("active")
        let inputMode = $(this).attr('id')
        if(inputMode == "textInput"){
            $(".speak-story").fadeOut(function(){
                $(".type-story").css("display","block") 
            })
        }
        else if(inputMode == "voiceInput"){
            $(".type-story").fadeOut(function(){
                $(".speak-story").css("display","block") 
            })
        }
    })

    

});