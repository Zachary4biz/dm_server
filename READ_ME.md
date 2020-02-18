### 增加一个新的TFServing服务

如果是普通类型的，例如一个独立的分类模型，直接做就行了
- `apps`里做好对应的服务
- `config.py` 里配置对应的 `CONFIG_NEW`
- `urls.py` 里加上对应的请求key

如果需要是需要ensemble，比如新的NSFW服务，是采用了bcnn分类+yolo检测两个模型，这两个各自是一个TFServing服务，所以新的NSFW服务需要
- 在`config.py`使用`Params`创建（其实就理解为一个类似cutcut_profile的服务）
- 大部分请求子服务（ensemble）相关的code都在`apps/nsfw_ensemble_service.py` 里完成
- 没有把所有模型配到一个TFServing里是因为尽管它有一些内部的并行管理，还是说出现阻塞，直接从根上就分成多个TFServing，后续迭代的TFServing应该可以更好的支持多模型并发请求，类似于yarn调度hadoop资源一样

启动顺序相关
- settings.py 和 urls.py 评级，不能互相import
- 实验发现 urls.py 里的assert都没有生效，是gunicorn启动的原因吗？
- config.py是最早的，可以在settings.py里进行import


关于服务名字的说明(service_name、CONFIG_NEW的key、各service.py的NAME)

`config.py`里
- `Params`的`service_name`在`_start_service_seperate.py`里用到，启动各个服务时`sh start.sh abc`所使用的`abc`就是`service_name` (`sh start.sh seq`同理)
- `CONFIG_NEW`的`key`是和各个service各自`xxx_service.py`的`NAME`对应的，各service使用自己的`NAME`获取`CONFIG_NEW`里对应的`Params`
- `cutcut_profile`里请求各个服务时，对结果的拼接用的是各自`xxx_service.py`的`NAME` (151L)


`services.py`作为模板，统一处理各个`xx_service.py`的`predict()`方法
- 直接在各自的`predict()`里调用`api_format_predict`
- 各个`xx_service.py`自有的逻辑，写一个单独的方法赋值给`api_format_predict`的`_predict`参数
- `_predict`接受的方法要求
  - 输入一个img(使用service自己提供的`load_img_func`加载得到)
  - 输出一个tuple=`(res,remark)`
    - res即返回结果，数组或字典都可以，`api_format_predict`里会直接用`json.dumps`序列化 (29L)
    - 无异常时remark标记为"success"，有异常记录异常信息

每个service都要提供自己加载图片的方法（考虑兼容caffe、tf等模型侧有特殊输入需求）给属性 `load_img_func` 
- 例如 `load_img_func = cvUtil.img_from_url_cv2`
- 在 `cvUtil` 中实现了`PIL`,`opencv-python`,`caffe.io`等加载方式


如果出现 `Page not found at /xxx` 检查`urls.py`是否配置正确（url里的regex字符串和key是不是对得上？）