$(document).ready(function(){
    var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr('value');

    $('.checkbox').on('click',function(){
        
        console.log($(this).prop('id'))
        let idData = $(this).attr('id').split('-')
        console.log(idData)
        $.ajax(({
            url:'/update-services/',
            headers: {'X-CSRFToken': $csrf_token},
            type:'POST',
            data:{
                'serviceType':idData[0],
                'operator':idData[1],
            },
            success:function(response){
                if(response['status'] == 'success'){
                    location.reload(true);
                }                
            }
            }))        
        
    })
    
   
    
})