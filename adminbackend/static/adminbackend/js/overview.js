$(document).ready(function(){
    // ATN Balance
    $.ajax({
        url:"/airtimeng-balance/",
        type:"GET",
        success:function(response){
            if(response['status'] == 'success'){
                $('#airtimeNG-preloader').css('display','none');
                $('#airtimeNG-balance').text(Number(response['data']).toLocaleString());
            }

        },
    });
    setInterval(function(){
        $('#airtimeNG-balance').html('');
        $('#airtimeNG-balance').css('display','none');
        $('#airtimeNG-preloader').css('display','block');
        $.ajax({
            url:"/airtimeng-balance/",
            type:"GET",
            success:function(response){
                if(response['status'] == 'success'){
                    $('#airtimeNG-preloader').css('display','none');
                    $('#airtimeNG-balance').text(Number(response['data']).toLocaleString());
                    $('#airtimeNG-balance').css('display','inline-block');
                }
    
            },
        });
    },20000)  

    // Honourworld Balance
    $.ajax({
        url:"/honourworld-balance/",
        type:"GET",
        success:function(response){
            if(response['status'] == 'success'){
                $('#honourwolrd-preloader').css('display','none');
                $('#honourwolrd-balance').text(Number(response['data']).toLocaleString());
            }

        },
    });
    setInterval(function(){
        $('#honourwolrd-balance').html('');
        $('#honourwolrd-balance').css('display','none');
        $('#honourwolrd-preloader').css('display','block');
        $.ajax({
            url:"/honourworld-balance/",
            type:"GET",
            success:function(response){
                if(response['status'] == 'success'){
                    $('#honourwolrd-preloader').css('display','none');
                    $('#honourwolrd-balance').text(Number(response['data']).toLocaleString());
                    $('#honourwolrd-balance').css('display','inline-block');
                }
    
            },
        });
    },20000) 


    // TWINS10 Balance
    $.ajax({
        url:"/twins10-balance/",
        type:"GET",
        success:function(response){
            if(response['status'] == 'success'){
                $('#twins10-preloader').css('display','none');
                $('#twins10-balance').text(response['data']);
            }

        },
    });
    setInterval(function(){
        $('#twins10-balance').html('');
        $('#twins10-balance').css('display','none');
        $('#twins10-preloader').css('display','block');
        $.ajax({
            url:"/twins10-balance/",
            type:"GET",
            success:function(response){
                if(response['status'] == 'success'){
                    $('#twins10-preloader').css('display','none');
                    $('#twins10-balance').text(response['data']);
                    $('#twins10-balance').css('display','inline-block');
                }
    
            },
        });
    },20000) 
});