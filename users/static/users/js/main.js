$(document).ready(function(){
    var $crf_token = $('[name="csrfmiddlewaretoken"]').attr('value');
    // Set Pin Button
    $(".setPIN").on('click',function(){
        setTransactionPIN()
    });

    $("#backSetPIN").on('click',function(){
        $('#confirmPinSet').fadeOut(function(){
            $('#setNewPIN').css('display','block')
        })
    })

    $("#backNewPIN").on('click',function(){
        $('#confirmNewPIN').fadeOut(function(){
            $('#setNewPIN').css('display','block')
        })
    })

    // Update PIN newPIN
    $(".updatePIN").on('click',function(){
        updateTransactionPIN()
    });

    // Set PIN Function
    window.setTransactionPIN = function(){
        let pin1 = ''
        let pin2 = ''
        $('#setTransactionPin').fadeIn()
        $(function(){
          $('#setPinwrapper').pinlogin({
            fields : 4, // default 5
            placeholder:'*', // default: '•'
            reset :true,
            complete :function(pin){
              pin1 = pin
              $('#setNewPIN').fadeOut(function(){
                $('#confirmPinSet').css('display','block')
                
                $(function(){
                  $('#confirmPinwrapper').pinlogin({
                    fields : 4, // default 5
                    placeholder:'*', // default: '•'
                    reset :true,
                    complete :function(pin_2){
                      pin2 = pin_2
                      if(pin1 === pin2){
                        $('#confirmSetpinvalidation').html('')
                        $('#confirmSetpinvalidation').css('display','none')
    
                        // $('#confirmPinSet').css('display','none')
                        $('.loader-overlay').css('display','flex')
                        $.ajax({
                          url:'/save-pin/',
                          type:'POST',
                          headers: {'X-CSRFToken': $crf_token},
                          data:{
                              'pin1':pin1,
                              'pin2':pin2,
                          },
                          success:function(response){
    
                              if(response.code === '00'){
                                $('#confirmPinSet').fadeOut(function(){
                                  $('#pinSetFeedback').fadeIn()
                                })
                                $('.loader-overlay').css('display','none')
                                
    
                              }
                          }
              
                      })
    
                      }
                      else{
                        $('#confirmSetpinvalidation').html('the transaction pin does not match')
                        $('#confirmSetpinvalidation').css('display','block')
                      }
                      
                        },
                    reset :true,
                  });
                })
    
              })
                },
          });
        })
        
    }

    // Update PIN Function
    window.updateTransactionPIN = function(){
        let oldPIN = ''
        let pin1 = ''
        let pin2 = ''
        $('#updateTransactionPin').fadeIn()
        $(function(){
            $("#oldPINWrapper").pinlogin({
                fields : 4, // default 5
                placeholder:'*', // default: '•'
                reset :true,
                complete:function(old_PIN){
                    oldPIN = old_PIN
                    // Show preloader
                    $('.loader-overlay').css('display','flex')
                    $.ajax({
                      url:'/check-pin/',
                      type:'GET',
                      data:{
                        'oldPIN':oldPIN
                      },
                      success:function(response){
                        console.log(response);
                        if(response.code == '00'){
                          $('.loader-overlay').css('display','none')
                          // Ask for new PIN
                          $("#oldTransPIN").fadeOut(function(){
                            $('#OldPINValidation').css('display','none')
                            $('#newPIN').css('display','block')
                            $(function(){
                                $('#newPINWrapper').pinlogin({
                                  fields : 4, // default 5
                                  placeholder:'*', // default: '•'
                                  reset :true,
                                  complete :function(pin){
                                    pin1 = pin
                                    $('#newPIN').fadeOut(function(){
                                      $('#confirmNewPIN').css('display','block')
                                      
                                      $(function(){
                                        $('#confirmNewPINWrapper').pinlogin({
                                          fields : 4, // default 5
                                          placeholder:'*', // default: '•'
                                          reset :true,
                                          complete :function(pin_2){
                                            pin2 = pin_2
                                            if(pin1 === pin2){
                                              $('#confirmNewPINValidation').html('')
                                              $('#confirmNewPINValidation').css('display','none')
                          
                                              // $('#confirmPinSet').css('display','none')
                                              $('.loader-overlay').css('display','flex')
                                              $.ajax({
                                                url:'/update-pin/',
                                                type:'POST',
                                                headers: {'X-CSRFToken': $crf_token},
                                                data:{
                                                    'oldPIN':oldPIN,
                                                    'pin1':pin1,
                                                    'pin2':pin2,
                                                },
                                                success:function(response){
                          
                                                    if(response.code === '00'){
                                                      $('#confirmNewPIN').fadeOut(function(){
                                                        $('#updatePINFeedback').fadeIn()
                                                      })
                                                      $('.loader-overlay').css('display','none') 
                                                    }
                                                    else if(response.code === '01'){
                                                        $('#confirmNewPIN').fadeOut(function(){
                                                            $("#oldTransPIN").css('display','block') 
                                                            $('#OldPINValidation').html('old transaction PIN entered is incorrect')
                                                            $('#OldPINValidation').css('display','block')
                                                        })
                                                        $('.loader-overlay').css('display','none') 
                                                      }
                                                }
                                    
                                            })
                          
                                            }
                                            else{
                                              $('#confirmNewPINValidation').html('the transaction PIN does not match')
                                              $('#confirmNewPINValidation').css('display','block')
                                            }
                                            
                                              },
                                          reset :true,
                                        });
                                      })
                          
                                    })
                                      },
                                });
                              })

                          })
                        }
                        else{
                          $('#OldPINValidation').html('old transaction PIN entered is incorrect')
                          $('#OldPINValidation').css('display','block')
                          $('.loader-overlay').css('display','none')
                        }
                      }
                    })

                    
                }
            })
        })
        
    }

    // When the user clicks anywhere outside of the modal, close it
    // window.onclick = function(event) {
    //     if (event.target.id == "updateTransactionPin" || event.target.id == 'closePINUpdate' ) {
    //         $("#updateTransactionPin").css("display","none");
    //         $("#newPIN").css("display","none");
    //         $("#confirmNewPIN").css("display","none");
    //         $("#oldTransPIN").css("display","block");
    //     }
    //     else if (event.target.id == "giveAwayFaq" ) {
    //         $("#giveAwayFaq").css("display","none");
    //     }
    //     else if (event.target.id == "referralModal" ) {
    //       $("#referralModal").css("display","none");
    //   };
    // };

    
})