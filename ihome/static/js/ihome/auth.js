function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
	$('#form-auth').submit(function(e){
        e.preventDefault();
        var real_name = $('#real-name').val();
        var id_card = $('#id-card').val();
        req_data = {
            real_name: real_name,
            id_card: id_card
        }
        req_json = JSON.stringify(req_data)
        $.ajax({
            url: '/api/v1.0/users/auth',
            type: 'post',
            data: req_json,
            contentType: 'application/json',
            dataType: 'json',
            headers:{
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (resp){
                if (resp.errno == 0){
                    // 上传成功
                    var real_name = resp.data.real_name
                    var id_card = resp.data.id_card
                    $('#real_name').text(real_name)
                    $('#id_card').text(id_card)
                }
                else{
                    alert(resp.errmsg)
                }
            }
        })
    })
})
