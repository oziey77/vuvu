$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    var identityType
    var verificationID


    // Date dropdown
    let dateDropdown = document.getElementById('date-year');

    let currentYear = new Date().getFullYear();
    let earliestYear = 1940;

    while (currentYear >= earliestYear) {
        let dateOption = document.createElement('option');
        dateOption.text = currentYear;
        dateOption.value = currentYear;
        dateDropdown.add(dateOption);
        currentYear -= 1;
    }

    
    // Genrate SafeHaven
    $("#generate-sfb").on("click",function(){
      $("#generateAccount").fadeOut(function(){
        $("#KYCForm").css('display','block')
      })
    })

    // ID TYPE
    $("#id_type").on('change',function(){
      let idType = $(this).val();
      if(idType != '' ){
        $("#idTypeError").html('');
        $("#idTypeValidation").css('display','none');
      }
    });

    // ID Number
    $("#id_num").bind("keyup focusout",function(){
      let IDNum = $(this).val()
      if(IDNum.length > 0){
        $("#idNumError").html('');
        $("#idNumValidation").css('display','none');
      }
    })

    // First name Number
    $("#first_name").bind("keyup focusout",function(){
      let IDNum = $(this).val()
      if(IDNum.length > 0){
        $("#firstNameError").html('');
        $("#firstNameValidation").css('display','none');
      }
    })

    // Last name Number
    $("#last_name").bind("keyup focusout",function(){
      let IDNum = $(this).val()
      if(IDNum.length > 0){
        $("#lastNameError").html('');
        $("#lastNameValidation").css('display','none');
      }
    })

    // Date of birth validation
    $("#date-day,#date-month,#date-year").on('change',function(){
      dobValid();
    });

    // KYC Logics
    $("#submit-kyc").on("click",function(e){
        e.preventDefault()
        let idType = false
        let idNum = false
        let firstName = false
        let lastName = false
        let dob = false
        // ID TYPE VALIDATION
        if($("#id_type").val() == ""){
          $("#idTypeError").html("please select your ID type")
          $("#idTypeValidation").css("display","block")
          
        }
        else{
          $("#idTypeError").html("")
          $("#idTypeValidation").css("display","none")
          identityType = $("#id_type").val() 
          idType = true
        }
  
        // ID NUMBER VALIDATION
        if($("#id_num").val() == ""){
          $("#idNumError").html("please enter a valid ID number")
          $("#idNumValidation").css("display","block")
        }
        else{
          let idNumber = $(this).val()
          console.log((Number($("#id_num").val()) * 1))
          if (isNaN(Number($("#id_num").val()) * 1)){
            $("#idNumError").html("please enter a valid ID number")
            $("#idNumValidation").css("display","block")
          }
          else{
            $("#idNumError").html("")
            $("#idNumValidation").css("display","none")
            idNum = true
          }        
        }
  
        // ID First Name VALIDATION
        if($("#first_name").val() == ""){
          $("#firstNameError").html("please enter your first name")
          $("#firstNameValidation").css("display","block")
        }
        else{
          $("#firstNameError").html("")
          $("#firstNameValidation").css("display","none")
          firstName = true
        }
  
        // ID Last Name VALIDATION
        if($("#last_name").val() == ""){
          $("#lastNameError").html("please enter your last name")
          $("#lastNameValidation").css("display","block")
        }
        else{
          $("#lastNameError").html("")
          $("#lastNameValidation").css("display","none")
          lastName = true
        }
  
        // ID DOB VALIDATION
        if($("#date-day").val() == "" || $("#date-month").val() == "" || $("#date-year").val() == ""){
          $("#dobError").html("please set a valid date of birth")
          $("#dobValidation").css("display","block")
        }
        else{
          $("#dobError").html("")
          $("#dobValidation").css("display","none")
          dob = true
        }
  
        if(idType && idNum && firstName && lastName && dob){
          $(".loader-overlay").css("display","flex")
          $("#error-message").html('')
          $("#KYCError").css("display","none")
  
          // subimt form
          let form = $('#kyc-form'),
          fd = new FormData(form.get(0))
  
          $.ajax({
            url: '/submit-kyc/',
            type: form.attr('method'),
            // contentType: 'multipart/form-data', 
            contentType: false,                   
            dataType: 'json',
            data: fd,
            headers: {'X-CSRFToken': $crf_token},
            processData: false,
            success:function(response){
              console.log(response)
              if(response.code == "00"){
                verificationID = response.verificationID
                $("#KYCForm").fadeOut(function(){
                  $("#OTPVerification").css("display","block")
                })
                
              }
              if(response.code == "09"){
                $("#error-message").html('')
                $("#KYCError").css("display","block")

              }
              $(".loader-overlay").css("display","none")
            }
          })
        }
  
        
    })

    // Copy one Time/Dynamic account number
    $('#copySfbAcc').click(function(e){
      e.preventDefault()
      // alert('COPY CLICKED')
      var copyBTN = $(this);
      var $temp = $("<input>");
      $("body").append($temp);
      $temp.val($('#sfbAccNo').text()).select();
      document.execCommand("copy");
      $temp.remove();
      $(copyBTN).css('display','none');
      $('#sfbcopyIndicator').css('display','block');
      setTimeout(function(){
        $('#sfbcopyIndicator').css('display','none');
        $(copyBTN).css('display','block');
      },1500);
    });

    // OTP verification
    $(function(){
        $('#PINWrapper').pinlogin({
          fields : 6, // default 5
          placeholder:'*', // default: '•'
          reset :false,
          complete :function(pin){
            sendOTP(pin)
              },
        });
      })

    //DOB validation 
    function dobValid(){
      let day = $("#date-day").val();
      let month = $("#date-month").val();
      let year = $("#date-year").val();
      if(day != '' && month != '' && year != ''){
        $("#dobValidation").css('display','none');
      }

      
    }

    // Send OTP
    function sendOTP(otpCode){
      $('#OTPError').html('')
      $('#OTPErrorContainer').css('display','none')
      $(".loader-overlay").css("display","flex")
      $.ajax({
        url: '/validate-kyc/',
        type: "POST",
        headers: {'X-CSRFToken': $crf_token},
        data: {
          "verificationID":verificationID,
          "otp":otpCode,
          "identityType":identityType
        },
        success:function(response){
          console.log(response)
            if(response.code=='00'){
              location.reload(true)
            }
            if(response.code=='09'){
              $('#OTPError').html(response.message)
              $('#OTPErrorContainer').css('display','block')
              $(".loader-overlay").css("display","none")
            }
            
        }

      })
    }

})