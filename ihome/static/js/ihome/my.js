function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
    $.ajax({
    	url: '/api/v1.0/session',
    	type: 'delete',
    	headers: {
    		"X-CSRFToken":getCookie("csrf_token")
    	},
    	dataType: "json",
    	success: function(resp){
    		if(resp.errno == '0'){
    			location.href = '/index.html';
    		}
    	}
    })
}

$(document).ready(function(){
    // 检查登录状态，获取用户信息
    $.get('/api/v1.0/users/profile', function(resp){
        if(resp.errno == '0'){
            // 获取用户信息成功
            $('#user-avatar').attr('src', resp.data.avatar_url)
            $('#user-name').text(resp.data.name)
            $('#user-mobile').text(resp.data.mobile)
        }
        else{
            // 此处应把未登录的错误信息单独列出并跳转，将其他错误放在一起
            alert(resp.errmsg)
            location.href = '/login.html';
        }
    })
})