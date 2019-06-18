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


$(document).ready(function () {
    $("#form-avatar").submit(function (e) {
        // 阻止表单的默认行为
        e.preventDefault();
        // 利用jquery.form.min.js提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({
            url: "/api/v1.0/users/avatar",
            type: "post",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 上传成功
                    var avatarUrl = resp.data.avatar_url;
                    $("#user-avatar").attr("src", avatarUrl);
                    showSuccessMsg();
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    })

    $('#form-name').submit(function(e){
        e.preventDefault();
        var name = $('#user-name').val();
        req_data = {
            name: name
        }
        req_json = JSON.stringify(req_data)
        $.ajax({
            url: '/api/v1.0/users/name',
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
                    var user_name = resp.data.name
                    $('#user_name').text(user_name);
                    showSuccessMsg();
                }
                else{
                    alert(resp.errmsg)
                }
            }
        })
    })
})