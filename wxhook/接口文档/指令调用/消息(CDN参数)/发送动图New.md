`2022年9月30日 新增`

**请求**

###### 1.1 使用文件发送

 ``` 
 {
  "type": 11254,
  "data": {
    "path": "d:\\test.gif",
    "to_wxid": "filehelper"
  }
} 

 ```
 
 ###### 1.2 使用md5参数发送
 

 ``` 
 {
  "type": 11254,
  "data": {
    "md5": "5190505E9E656BF0E72CBBF2DAA01C4F",
    "size": 410883,
    "to_wxid": "filehelper"
  }
} 

 ```





**返回**

 ``` 
 {
  "data": {
    "actionFlag": 0,
    "baseResponse": {
      "errMsg": {},
      "ret": 0
    },
    "emojiItem": [
      {
        "md5": "5190505E9E656BF0E72CBBF2DAA01C4F", // 文件md5
        "msgId": 774295222,
        "newMsgId": "6982243159xxxxxx2897416",  // 消息id
        "ret": 0,  // 用于判断是否发送成功 0 成功
        "startPos": 410883,
        "totalLen": 410883         // 文件长度
      }
    ],
    "emojiItemCount": 1
  },
  "type": 11254
} 

 ```

