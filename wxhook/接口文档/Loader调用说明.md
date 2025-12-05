**DLL接口**

DLL有两个`Loader.dll`和`Helper.dll`

**DLL文件说明：** 

|文件名|说明|
|:----    |:---|
|Loader.dll | 管理端，用于多开微信和与微信交互  |
|Helper.dll |客户端，接收指令并发送数据给管理端  |

`WeChatHelper.dll可以以微信版本号做为名称，先使用GetUserWeChatVersion函数获取用户电脑上的微信版本，判断是否支持，如果支持，使用InjectWeChat注入dll`


**Loader.dll的导出函数:**

1. InitWeChatSocket
	`用于socket的回调处理`
	函数原型：
	`BOOL __stdcall InitWeChatSocket(IN DWORD dwConnectCallback, IN DWORD dwRecvCallback, IN DWORD dwCloseCallback)`
	其中dwConnectCallback是一个函数指针类型, 在有新客户端加入时调用，结构如下：
		`void __stdcall MyConnectCallback(int iClientId)` 传入的一个参数是socket的客户ID,返回值为空 
	dwRecvCallback是一个函数指针类型,在接收到新消息时调用，结构如下：
		`void __stdcall MyRecvCallback(int iClientId, char* szJsonData, int iLen)` 
	dwCloseCallback是一个函数指针类型，在客户端退出时调用，结果如下:
		`void __stdcall MyCloseCallback(int iClientId)`

2. GetUserWeChatVersion
	`获取当前用户的电脑上安装的微信版本，如： 2.6.7.57`
	函数原型：
	`BOOL __stdcall GetUserWeChatVersion(OUT LPSTR szVersion);`
	传一个ANSI字符串缓冲区的指针，长度30即可， 这个函数可以先获取当前用户电脑上安装的微信版本，然后判断我们的dll是否支持，如果不支持就提示用户下载我们支持的版本。
	
3. InjectWeChat
	`用于智能多开，并注入dll, 注入成功返回微信的进程ID, 失败返回0`
	函数原型：
	`DWORD __stdcall InjectWeChat(IN LPCSTR szDllPath);`
	如果需要一个软件，管理多个微信，多次调用这个函数实现，通过socket回调管理客户端

4. SendWeChatData
	用于向微信发送指令，指令内容参考功能类，·
	函数原型:
	` BOOL __stdcall SendWeChatData(IN CONNID dwClientId, IN LPCSTR szJsonData);`
	
5. DestroyWeChat
	`主程序退出前，执行释放函数，用于卸载DLL和关闭socket服务端`
	函数原型:
	`BOOL __stdcall DestroyWeChat();`
	
6. UseUtf8
	`在所有接口前执行，执行后接口全部使用utf8编码传输`
	函数原型:
	`BOOL __stdcall UseUtf8();`
	
7. InjectWeChat2
	`用于智能多开,跟InjectWeChat功能相同，多了一个参数传递指定微信的安装路径，并注入dll, 注入成功返回微信的进程ID, 失败返回0`
	函数原型：
	`DWORD __stdcall InjectWeChat(IN LPCSTR szDllPath, IN LPCSTR szWeChatExePath);`
	如果需要一个软件，管理多个微信，多次调用这个函数实现，通过socket回调管理客户端
	
8. InjectWeChatPid
	`注入指定的微信进程，参数1： 微信进程id, 参数2： dll路径`
	函数原型：
	`DWORD __stdcall InjectWeChatPid(IN DWORD dwPid, IN LPCSTR szDllPath)`
	

9. InjectWeChatMultiOpen
	`多开一个新的微信进程并注入，不维护已经打开的微信进程，需要两个参数，参数1：WeChatHelper.dll的路径，参数2：指定要启动微信（WeChat.exe）的完整路径，如果不提供，可以设置0或空字符串，将自动读取微信的安装目录`
	函数原型：
	`DWORD __stdcall InjectWeChatMultiOpen(IN LPCSTR szDllPath, IN LPCSTR szWeChatExePath);`·

