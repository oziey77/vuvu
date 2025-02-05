$(document).ready(function(){
    console.log("connected")
    
    // Update Last activity
    setInterval(function(){
        $.ajax({
            url:"/update-last-activity/",
            type:"GET",
            success:function(response){
                console.log(response)
            }
        })
    },60000)
    
})