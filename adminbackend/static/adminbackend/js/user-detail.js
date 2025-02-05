$(document).ready(function(){
    console.log("usre ")
    $(".wallet-action-btn").on("click",function(){
        let id = $(this).prop("id");
        $(".wallet-action-btn").removeClass("active");
        $(this).addClass("active");
        if(id=="creditBTN"){            
            $("#debitForm").css("display","none");
            $("#creditForm").css("display","block");
        }
        else if(id=="debitBTN"){  
            $("#creditForm").css("display","none");          
            $("#debitForm").css("display","block");            
        }
        
    })
})