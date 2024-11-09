$(document).ready(function(){
    var iconBox;
    var operatorImg;
    var selectedOperator;
    var operatorName;

    // Network operator validator
    var AirtelInitials = ['0911','0912','0907','0904','0902','0901','0812','0808','0802','0708','0701']
    var MTNInitials = ['0916','0913','0906','0903','0816','0814','0813','0810','0806','0803','0706','0704','0703','0702','0702']
    var GLOInitials = ['0915','0905','0815','0811','0807','0805','0705']
    var N9MobileInitials = ['0908','0909','0818','0817','0809']

    // Set bottom nav Icon
    $("#dashboardNormal").css('display','none')
    $("#dashboardActive").css('display','block')
    // Scroll image
    $( ".slider-container" ).scrollLeft( 290 );
    // Fetch wallet balance at interval
    function setIntervalLimited(callback, interval, x) {

        for (var i = 0; i < x; i++) {
            setTimeout(callback, i * interval);
        }
    
      }
    setIntervalLimited(function() {
        $.ajax({
          url:"/user-balance/",
          type:"GET",
          success:function(response){
            $("#mainBalance").html(Number(response.balance).toLocaleString(undefined,{minimumFractionDigits:2}));
            // data = JSON.parse(response)
            // $('.balance').text(Number(data['balance']).toLocaleString())
          }
        })          
      }, 3000, 2);

      $(".dash-nav").on("click",function(){
        $("#linkLoading").css("display","flex")
      })

    // Give Away 
    let giveAwayProgress = $("#userGiveAwayProgress").val()
    $("#progressRate").css("width",`${giveAwayProgress}%`)
    $("#giveAwayBTN").on('click',function(){
      $("#giveAwayFaq").css('display','block');
    })

    // Cashback
    $(".redeem-BTN").on('click',function(){
      let id = $(this).attr('id').split('-')[0];
      if(id !='' && id != undefined){
        $(this).css('display','none');
        $(`#${id}-preloader`).css('display','block')
        // Ajax
        $.ajax({
          url:"/redeem-cashback/",
          type:"GET",
          data:{
            "type":id
          },
          success:function(response){
            if(response.code == '00'){
                          
              $(`#${id}-BTN`).removeClass('redeem-BTN');
              $(`#${id}-BTN`).addClass('disabled');              
              $(`#${id}-preloader`).fadeOut(function(){
                $(`#${id}-Feedback`).css('display','block');
              });  
              setTimeout(function(){
                $(`#${id}-Feedback`).css('display','none');
                $(`#${id}-BTN`).css('display','block');
                $(`#${id}-BTN`).attr("id","");
              },4000)
              
              $("#mainBalance").html(Number(response.balance).toLocaleString(undefined,{minimumFractionDigits:2}));
              $(`#${id}-balance`).html(Number(response.bonusBalance).toLocaleString(undefined,{minimumFractionDigits:2}));
            }
          }
        })
      }
      
    })

    // Referral
    $("#openRefModal").on('click',function(){
      $("#referralModal").css('display','block');
    })

    // Referral message copy
    $("#copy-ref-messg").on('click',function(e){
      e.preventDefault()
      var $temp = $("<textarea>");
      $("body").append($temp);
      $temp.val($('#referral-mssg').text()).select();
      document.execCommand("copy");
      $temp.remove();
      $(this).css("display",'none')
      $(".ref-message-feedback").css("display",'block')
      setTimeout(function(){
        $(".ref-message-feedback").css("display",'none')
        $("#copy-ref-messg").css("display",'block')
      },2000)
  })

  // Claim Give Away
  $('#claimGiveAway').on('click',function(){
    $('#giveAwayModal').css('display','block')
  })
  // network selector
  $("#network-selector").on('click',function(){
    // $("#network-dropdown").css("display","block");
    $("#network-dropdown").fadeIn();
    iconBox = $(this).find('#selectedOperatorImg')[0];
    operatorImg = $(this).find('img')[0];
    operatorName = $(this).find('p')[0];
  })

  // Select Operator
  $(".mobile-operator").on('click',function(){
    // $("#amount").text('');
    $('#error-message').text(``)
    $('.error-feedback').css('display','none')
    selectedOperator = $(this).attr('network-data');
    var selectedOperatorImg = $(this).attr('image-data');
    $(".operator-text").html(selectedOperator);
    $(operatorImg).attr('src',selectedOperatorImg);
    $("#selectedOperatorImg").css('display','block');
    $("#phone_number").val('')
    $("#network-dropdown").fadeOut();

    // Set Operator discount
    // $.each(discountData,function(key,value){
    //     if(value.networkOperator == selectedOperator){
    //         discountRate = Number(value.rate)
    //         console.log(discountRate);
    //     };
        
    // });

    
});

// Phone Number Input Logic
  $("#phone_number").bind('focusout keyup',function(){
    // if (inputValid()){
    //     $("#buyData").removeClass('disabled');
    // }
    // else{
    //     $("#buyData").addClass('disabled');
    //     $("#buyData").attr('disabled',true);
    // }
    inputValid()
  });

  $("#processGiveAway").on("click",function(e){
    e.preventDefault()
    if(recipientValid()){
      $(".loader-overlay").css("display","flex")
      // Ajax
      $.ajax({
        url:"/claim-giveaway/",
        type:"GET",
        data:{
          "selectedOperator":selectedOperator,
          "recipient":$("#phone_number").val()
        },
        success:function(response){
          $(".loader-overlay").css("display","none")
          console.log(response)
          if(response.code == "00"){
            $("#transactionFeedback").css("display","block")
          }
          else if(response.code == '09'){
            $(".error-message").html(response.message);
            // $(".error-feedback").slideUp()
            $(".error-feedback").css('display','block');
            // $("#purchaseData").attr('disabled',false);
            // $('#PINValidation').fadeOut()
        };
        }
      })
    }
  })



  // 
  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    if (event.target.id == "PINValidation" || event.target.id == 'closePINValidation' || event.target.id == 'transactionFeedback' || event.target.id == 'billSummary') {
        // $("#PINValidation").css("display","none");
        // $(".setting-modal").css("display","none");
        
    }
    else if(event.target.id == "giveAwayFaq"){
        $("#giveAwayFaq").css('display','none')
    }
    else if(event.target.id == "giveAwayModal"){
      $("#giveAwayModal").css('display','none')
    }
    else if(event.target.id == "referralModal"){
      $("#referralModal").css('display','none')
  }
  };

  // Operator Validation
  function recipientValid(){
    let pNum = $('#phone_number').val().substring(0,4)
    if (selectedOperator == 'Airtel'){
        if(jQuery.inArray(pNum, AirtelInitials) == -1) {
            $('#error-message').html(`Please enter a valid Airtel number`)
            $('.error-feedback').css('display','block')
            // setTimeout(function(){
            //     $('.validation').css('display','none')
            // },3000)
            return false
        }
        else{
            return true
        }
        
    }
    if (selectedOperator == 'MTN'){
        if(jQuery.inArray(pNum, MTNInitials) == -1) {
            $('#error-message').text(`Please enter a valid MTN number`)
            $('.error-feedback').css('display','block')
            // setTimeout(function(){
            //     $('.validation').css('display','none')
            // },3000)
            return false
        }
        else{
            return true
        }
        
    }
    if (selectedOperator == 'Glo'){
        if(jQuery.inArray(pNum, GLOInitials) == -1) {
            $('#error-message').text(`Please enter a valid Glo number`)
            $('.error-feedback').css('display','block')
            // setTimeout(function(){
            //     $('.validation').css('display','none')
            // },3000)
            return false
        }
        else{
            return true
        }
       
    }
    if (selectedOperator == '9Mobile'){
        if(jQuery.inArray(pNum, N9MobileInitials) == -1) {
            $('#error-message').text(`Please enter a valid 9Mobile number`)
            $('.error-feedback').css('display','block')
            // setTimeout(function(){
            //     $('.validation').css('display','none')
            // },3000)
            return false
        }
        else{
            return true
        }
        
    }
  }

  // Input field validation
  function inputValid(){
    let phoneNum = $("#phone_number").val();
    let planID = $("#dataPlans").val();
    if($(".operator-text").html() != "Select a network"){
        if(phoneNum.length == 11){
            $("#processGiveAway").removeClass('disabled');
            $("#processGiveAway").attr('disabled',false);
            return true;
        }
        else{
            $("#processGiveAway").attr('disabled',true);
            $("#processGiveAway").addClass('disabled');
            return false;
            
        }
    }
    else{
        $("#processGiveAway").attr('disabled',true);
        return false;        
    }
    
};

    
});