$(document).ready(function(){
    
    // Update Last activity
    setInterval(function(){
        $.ajax({
            url:"/update-last-activity/",
            type:"GET",
            success:function(response){
            }
        })
    },60000)
    
})