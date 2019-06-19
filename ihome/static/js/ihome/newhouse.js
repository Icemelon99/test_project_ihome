function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // 向后端获取城区信息
    $.get('/api/v1.0/areas', function(resp){
    	if(resp.errno == '0'){
    		// 获取成功
    		var areas = resp.data;
    		// 后端填充数据
    		// for (i=0; i<areas.length; i++){
    		// 	var area = areas[i]
    		// 	$('#area-id').append('<option value='+area.aid+'>'+area.aname+'</option>')}

    		// 使用前端模板填充数据
    		var html = template('area-tmpl', {areas: areas})
    		$('#area-id').html(html)
    	}
    	else{
    		alert(resp.errmsg)
    		location.href = '/index.html'
    	}
    })

    // 此处应先校验输入数据及格式
    // 处理收集到的数据
    $('#form-house-info').submit(function(e){
    	e.preventDefault();
    	// 处理表单数据
    	var data = {}
    	$('#form-house-info').serializeArray().map(function(x){
    		data[x.name] = x.value
    	})

    	// 处理设施
    	var facility = []
    	$(':checked[name=facility]').each(function(index, x){
    		facility[index] = $(x).val()
    	})
    	data.facility = facility

    	$.ajax({
    		url: '/api/v1.0/houses/info',
    		type: 'post',
    		contentType: 'application/json',
    		data: JSON.stringify(data),
    		dataType: 'json',
    		headers: {
    			'X-CSRFToken': getCookie('csrf_token')
    		},
    		success: function(resp){
    			if(resp.errno == '4101'){
    				// 用户未登录
    				alert(resp.errmsg)
    				location.href = '/index.html'
    			}
    			else if(resp.errno == '0'){
    				// 隐藏基本表单，显示图片表单
    				$('#form-house-info').hide()
    				$('#form-house-image').show()
    				// 设置图片表单的house_id字段
    				$('#house-id').val(resp.data.house_id)
    			}
    			else{
    				alert(resp.errmsg)
    			}
    		}
    	})
    })

    // 处理上传房屋图片
    $('#form-house-image').submit(function(e){
    	e.preventDefault();
    	$(this).ajaxSubmit({
    		url: '/api/v1.0/houses/image',
    		type: 'post',
    		dataType: 'json',
    		headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function(resp){
            	if(resp.errno == '4101'){
            		alert(resp.errmsg)
            		location.href = '/index.html'
            	}
            	else if(resp.errno == '0'){
            		$('.house-image-cons').append('<img src="'+resp.data.image_url+'" />')
            	}
            	else{
            		alert(resp.errmsg)
            	}
            }
    	})
    })
})