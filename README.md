# CLOG API



## 全局错误码

```python
ok = 1000
not_existed = 1001
has_existed = 1002
insert_fail = 1003
del_fail = 1004
lack_param = 1005
update_fail = 1006
database_error = 1007
timeout = 1008
frequent = 1009
server_error = 1010
auth_fail = 1011
verify_code_incorrect = 1012
password_incorrect = 1013
user_has_existed = 1014
full_size = 1015
param_error = 1016
```



## 文件服务

### 类型定义

#### UpFile

| Params                                  | Required | Type   | Description                            |
| --------------------------------------- | -------- | ------ | -------------------------------------- |
| name                                    | Y        | String | 文件名                                 |
| md5                                     | N        | String | 文件的MD5值， type 为文件夹时不需要    |
| <font color=#1E90FF>in_file</font>      | N        | Int    | 0/1                                    |
| <font color=#1E90FF>directory_id</font> | N        | Int    | 上传的位置，文件夹Id。不填或-1为根目录 |
| <font color=#1E90FF>type</font>         | N        | Int    | 0：文件 1：文件夹 (不填默认是0)        |
| <font color=#FF69B4>in_album</font>     | N        | Int    | 0/1                                    |
| <font color=#FF69B4>album_id</font>     | N        | Int    | 上传的相册Id, 不填或-1代表默认相册     |

```json
{
    "name": "风灵玉秀.png",
    "md5": "beb652fa8ff10c573818fabb53605a66",
    "in_file": 1,
    "directory_id": -1,
    "type": 0
}
{
    "name": "新建文件夹1",
    "in_file": 1,
    "directory_id": -1,
    "type": 1
}
```

#### FileInfo

```json
{			
	"directory_id": -1,
	"directory_path": ",,",
	"file_id": 429,
	"filename": "风灵玉秀_d247a276-54db-11eb-9078-c4b301d16e91.png",
	"hash": "3dc4a30c89b3895ff00f653613699322",
	"id": 349, // 用户文件Id，不是文件Id
	"mime": "image/png",
	"name": "风灵玉秀.png",
	"size": "442510",
	"type": 0,
	"add_timestamp": 1611900288686,
	"update_timestamp": 1611900288686
}

{
	"directory_id": -1,
	"directory_path": ",,",
	"file_id": null,
	"id": 358,
	"name": "新建文件夹1",
	"type": 1,
	"update_timestamp": 1611906450786,
  "add_timestamp": 1611906450786,
}
```

#### PicInfo

```json
{
  "id": 182, // 相片Id
  "album_id": 0,
  "url": "/file/好起来了_f32cbe0e_quality.jpg",
  "exif_timestamp": null,
  "timestamp": 1609956410981
}
```

#### NormalInfo

```json
{
	"filename": "编组_32b89428-6209-11eb-82c9-c4b301d16e91.png",
	"hash": "c808d69aea07188db874671ee308accb",
	"id": 445, // 文件Id
	"mime": "image/png",
	"size": "37977"
}
```



### 文件秒传

**Description**

- 检查文件MD5，如果文件服务器上有相同的，则上传成功返回文件信息，存入用户的文件列表或相册。
- 当上传到相册时，如果文件表中的文件原本标记为临时文件，则修改为永久文件

**URL**

- `/file/fastUpload`

**Auth**

- session

**Method**

- Post

**参数说明**

| Params       | Required | Type   | Description                        |
| ------------ | -------- | ------ | ---------------------------------- |
| files | Y | Dict <FILEKEY, UpFile> | 文件列表 |

**返回值**

| Params             | Required | Type                                          | Description           |
| ------------------ | -------- | --------------------------------------------- | --------------------- |
| code               | Y        | Int                                           | 错误码                |
| data               | Y        | Dict                                          | 返回的数据            |
| data[FILEKEY].file | Y        | **FileInfo** or **PicInfo** or **NormalInfo** | 对应FILEKEY的文件信息 |
| data[FILEKEY].code | Y        | Int                                           | 错误码                |

#### 请求参数示例

```json
{
    "files":{
        "pic":{
            "name":"风灵玉秀.png",
            "md5":"3dc4a30c89b3895ff00f653613699322",
            "in_file":1,
            "directory_id":-1,
            "type":0
        },
        "video":{
            "name":"【2016拜年祭单品】婕纶二重奏.mp4",
            "md5":"beb652fa8ff10c573818fabb53605a66",
            "in_file":1,
            "directory_id":-1,
            "type":0
        },
      	"dir":{
				    "name": "新建文件夹1",
				    "in_file": 1,
				    "directory_id": -1,
				    "type": 1
				}
    }
}
```

#### 返回参数示例

```json
{
    "code": 1000,
    "data": {
        "pic": {
            "file": {
                "directory_id": -1,
                "directory_path": ",,",
                "file_id": 429,
                "filename": "风灵玉秀_d247a276-54db-11eb-9078-c4b301d16e91.png",
                "hash": "3dc4a30c89b3895ff00f653613699322",
                "id": 349,
                "mime": "image/png",
                "name": "风灵玉秀.png",
                "size": "442510",
                "type": 0,
                "add_timestamp": 1611900288686,
                "update_timestamp": 1611900288686
            },
            "code": 1000
        },
        "video": {
            "file": null,
            "code": 1001
        },
      	"dir": {
          	"file": {
                "id": 348,
                "type": 1,
                "directory_path": ",,",
                "directory_id": -1,
                "name": "新建文件夹1",
                "add_timestamp": 1611899748497,
                "update_timestamp": 1611899748497
          	},
            "code": 1000
				},
      }
    }
}
```

### 文件上传

**Description**

- 文件上传。如果 in_file是1 存入文件表（非永久）和用户文件表，如果 in_album 是1，存入文件表（永久）和相册表

**URL**

- `/file/upload`

**Auth**

- session

**Method**

- Post

**参数说明**

| Params | Required | Type | Description         |
| ---------- | -------- | -------- | ------------------------------- |
| {FILEKEY} | Y      | Data | 文件流 |
| fileUpInfo | Y | Dict<FILEKEY: UpFile> | 文件信息 (type 不需要，这个接口只能传文件) |

**返回值**

| Params             | Required | Type                                          | Description |
| ------------------ | -------- | --------------------------------------------- | ----------- |
| code               | Y        | Int                                           | 错误码      |
| data               | Y        | Dict                                          | 返回的数据  |
| data[FILEKEY].file | N        | **FileInfo** or **PicInfo** or **NormalInfo** | 文件信息    |
| data[FILEKEY].code | Y        | Int                                           | 错误码      |

#### 请求参数示例

```json
{
    "key1": {File1},
    "image2": {File2},
    "fileAttrs": {
      	"key1": {
          "name": "风灵玉秀.png",
    			"md5": "3dc4a30c89b3895ff00f653613699322",
    			"in_file": 1,
    			"directory_id": -1,
    			"type": 0
        },
      	"image2": {
          "name": "好起来了.jpg",
    			"md5": "beb652fa8ff10c573818fabb53605a66",
    			"in_file": 1,
    			"directory_id": -1,
    			"type": 0
        }
    }
}
```

#### 返回参数示例

```json
{
    "code": 1000,
    "data": {
        "key1": {
            "file": {
                "directory_id": -1,
                "directory_path": ",,",
                "file_id": 429,
                "filename": "风灵玉秀_d247a276-54db-11eb-9078-c4b301d16e91.png",
                "hash": "3dc4a30c89b3895ff00f653613699322",
                "id": 349,
                "mime": "image/png",
                "name": "风灵玉秀.png",
                "size": "442510",
                "type": 0,
                "add_timestamp": 1611900288686,
                "update_timestamp": 1611900288686
            },
            "code": 1000
        },
        "image2": {
            "file": null,
            "code": 1001
        }
    }
}
```

### 所有文件列表

**Description**

- 获取文件夹下的所有文件以及文件夹路径

**URL**

- `/file/user/list`

**Auth**

- session

**Method**

- Get

**参数说明**

| Params       | Required | Type   | Description                                |
| ------------ | -------- | ------ | ------------------------------------------ |
| directory_id | Y        | Int    | 文件夹ID，-1 代表根目录                    |

**返回值**

| Params | Required | Type            | Description          |
| ------ | -------- | --------------- | -------------------- |
| files  | Y        | Array<FileInfo> | 文件列表             |
| path   | N        | Array<String>   | 此文件夹的各级路径名 |
| code   | Y        | Int             | 错误码               |

### 文件夹列表

**Description**

- 获取文件夹下的所有文件夹以及文件夹路径

**URL**

- `/file/user/directory_list`

**Auth**

- session

**Method**

- Get

**参数说明**

| Params       | Required | Type | Description             |
| ------------ | -------- | ---- | ----------------------- |
| directory_id | Y        | Int  | 文件夹ID，-1 代表根目录 |

**返回值**

| Params | Required | Type             | Description |
| ------ | -------- | ---------------- | ----------- |
| files  | Y        | Array <FileInfo> | 文件列表    |
| code   | Y        | Int              | 错误码      |

### 搜索

**Description**

- 搜索文件

**URL**

- `/file/user/search`

**Auth**

- session

**Method**

- Get

**参数说明**

| Params | Required | Type   | Description  |
| ------ | -------- | ------ | ------------ |
| name   | Y        | String | 包含的文件名 |

**返回值**

| Params | Required | Type            | Description |
| ------ | -------- | --------------- | ----------- |
| files  | Y        | Array<FileInfo> | 文件列表    |
| code   | Y        | Int             | 错误码      |

### 删除

**Description**

- 删除文件或文件夹
- 当file表没有被user_file引用时，会去删除file表和硬盘上真实的文件
- 删除文件的操作会放在异步线程内，不保证成功

**URL**

- `/file/user/del`

**Auth**

- session

**Method**

- Post

**参数说明**

| Params | Required | Type | Description |
| ------ | -------- | ---- | ----------- |
| id     | Y        | Int  | 文件ID      |

**返回无data**



### 修改属性

**Description**

- 修改文件属性

**URL**

- `/file/user/set`

**Auth**

- session

**Method**

- Post

**参数说明**

| Params | Required | Type   | Description |
| ------ | -------- | ------ | ----------- |
| id     | Y        | Int    | 文件ID      |
| name   | N        | String | 文件名      |

**返回无data**



### 移动

**Description**

- 修改文件属性

**URL**

- `/file/user/move`

**Auth**

- session

**Method**

- Post

**参数说明**

| Params | Required | Type | Description      |
| ------ | -------- | ---- | ---------------- |
| id     | Y        | Int  | 文件ID           |
| to_id  | Y        | Int  | 移动到的文件夹ID |

**返回无data**



### 根据ID下载文件

**Description**

- 下载文件

**URL**

- `/file/user/get/{id}`

**Auth**

- session

**Method**

- Get

**参数说明**

| Params      | Required | Type   | Description                                     |
| ----------- | -------- | ------ | ----------------------------------------------- |
| id          | Y        | Int    | 文件ID                                          |
| quality     | N        | String | "low": 低质量图片压缩较大, "high": 高质量图片     |
| side        | N        | Int    | 图片最大边长                                     |
| size        | N        | Int    | 图片大小 （优先级大于 quality）                   |
| sf          | N        | Int    | 屏幕缩放倍率，会放大图片返回，gif图片不会应用缩放   |
| cover       | N        | Int    | 1：获取文件的预览图 0: 获取原始文件               |

**返回值**

正常情况下返回文件流，错误时返回标准的JSON格式，无 data



### 根据文件名下载文件

**Description**

- 下载文件

**URL**

- `/file/{filename}`

**Auth**

- 不需要验证

**Method**

- Get

**参数说明**

无参数

**返回值**

返回文件流

