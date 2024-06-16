# GalScriptTool
提取脚本的一些辅助提取代码

## 双行文本解析与写入 **txt_twoline_parse.py**

用于EntisGLS引擎CSX提取后的TXT文本解析，生成 JSON 文件，或者把翻译好的 JSON 文件写入到脚本中。
需要用到以下两个工具：
- 提取CSX:[GARbro](https://github.com/crskycode/GARbro)
- CSX解析: [EntisGLS_Tools](https://github.com/crskycode/EntisGLS_Tools)

主要是解决使用 [SExtractor](https://github.com/satan53x/SExtractor) 不方便处理 `name` 在 `message` 之后的情况。 

#### config.ini 配置文件
配置文件默认为 config.ini，编辑配置文件修改正则表达式，
根据配置文件中的正则表达式规则，解析文本文件并生成`[{name,message}]`格式 JSON 文件，或根据翻译文件替换文本文件中的内容。

```config.ini
startline=0

00_skip=^◆.+?◆([\x00-\x7F])
01_search=^◆.+?◆(?P<msg>[^「『（].*[。！？、‥])$
02_search=^◆.+?◆(?P<msg>[「『（].*)$
03_search=^◆.+?◆(?P<name>[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF].*)$

sample=表示以下全是注释不进行解析。
解析格式：

◇00099A2A◇別に寂しいとか、そんなんじゃない‥‥‥ただ単に暇なだけ、ホントにそれだけだ。
◆00099A2A◆別に寂しいとか、そんなんじゃない‥‥‥ただ単に暇なだけ、ホントにそれだけだ。

◇00099AB9◇「この歳になって寂しいとか‥‥‥ないわ」
◆00099AB9◆「この歳になって寂しいとか‥‥‥ないわ」

◇00099AE8◇真樹
◆00099AE8◆真樹

◇00099B28◇コンビニに寄って晩メシの弁当と、朝メシにパンでも～とか考えながら歩いていると‥‥‥
```

- startline：表示文件起始处理行数，默认为0。
- 00_skip：跳过匹配到的行。
- 01_search、02_search、03_search：匹配的正则规则，支持命名捕获组 ?P<msg> 和 ?P<name>。

配置文件参考项目 [SExtractor](https://github.com/satan53x/SExtractor)


#### 提取模式
从输入文件中提取数据并保存到 JSON 文件中。

`python script.py extract -i input.txt`
可选参数
- -o 或 --output：输出 JSON 文件（默认为 input.json）。
- -c 或 --config：配置文件（默认为 config.ini）。
- -s 或 --startline：起始行（覆盖配置文件中的值）。

#### 写入模式
根据翻译文件中的内容替换输入文件中的匹配文本，保存结果到新的文件中。

`python script.py insert -i input.txt`
可选参数
- -o 或 --output：输出 JSON 文件（默认为 input.json）。
- -c 或 --config：配置文件（默认为 config.ini）。
- -s 或 --startline：起始行（覆盖配置文件中的值）。
- -t 或 --translate：翻译文件（默认为 input.trans.json）。

#### 代码示例
假设有如下输入文件 input.txt：
```
◆0009992A◆这是一个测试信息。
◆0009992B◆这是另一个测试信息。

◆00099AB9◆「这是一个测试对话。」
◆00099AE8◆姓名XXX
```
并且有对应的翻译文件 input.trans.json：

```json
[
    {"message": "这是一个翻译后的测试信息。"},
    {"message": "这是翻译后的另一个测试信息。"},
    {"name":"翻译后的姓名XXX", "message": "「这是翻译后的另一个测试对话。」"}
]
```

执行命令：
`python script.py insert -i input.txt`

将生成一个新的文件 input.new.txt，内容如下：
```
◆0009992A◆这是一个翻译后的测试信息。
◆0009992B◆这是翻译后的另一个测试信息。

◆00099AB9◆「这是翻译后的另一个测试对话。」
◆00099AE8◆翻译后的姓名XXX
```
