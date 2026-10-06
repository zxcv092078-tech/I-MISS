爱弥斯 · AI陪伴聊天App
一个基于大模型的私人陪伴聊天App:自带记忆、支持拍照/语音消息、人设可自定义。
! 本项目不提供任何API密钥,也不提供现成的后端服务器。你需要自己申请大模型API账号、自己运行后端(本地或自己的服务器),才能让这个App正常工作。这是一套"自己动手搭建"的模板代码,不是开箱即用的产品。
这个项目包含什么
backend/   后端服务(Python + FastAPI):大模型对话、记忆、语音识别/合成
app/       手机App(React Native + Expo)
开始之前,你必须准备好这两样东西
1. 你自己的大模型API Key
本项目不内置、不提供任何API密钥。你需要自己去以下任一平台注册账号、申请Key、自己充值:
SiliconFlow 硅基流动(国内,手机号注册,有免费额度)
Moonshot Kimi开放平台
阿里云百炼
OpenAI(海外用户,需要信用卡/借记卡)
拿到Key后,填进 backend/.env(从 backend/.env.example 复制一份改名):
LLM_API_KEY=你的key
LLM_BASE_URL=你选的平台对应的地址
LLM_MODEL=你选的模型名
这是你自己的账号和余额,所有调用产生的费用由你自己承担。
2. 一个能被手机访问到的后端地址
这个App不会自动帮你托管后端,你必须自己让 backend/ 这个服务跑起来,并且手机要能连得到它。两种方式二选一:
方式A:本地跑(免费,但有限制)
在你电脑上运行后端(uvicorn server:app --host 0.0.0.0 --port 8000)
手机和电脑必须连同一个局域网(同WiFi,且路由器不能开"AP隔离"这类阻止设备互联的功能)
缺点:电脑关机、不在同一网络下,App就用不了;打包APK时填的IP地址是你电脑当时的局域网IP,换网络环境后需要重新打包
方式B:部署到云服务器(推荐,稳定,但要花钱)
租一台云服务器(阿里云/腾讯云/Vultr等均可),把 backend/ 部署上去,24小时跑着
用服务器的公网IP,不受你电脑和网络环境影响
打包App时,必须填入你自己的后端地址
打开 app/screens/ChatScreen.js,找到这一行:
const BACKEND_URL = "http://192.168.1.XXX:8000";
用方式A(本地):改成你电脑当时的局域网IP,例如 http://192.168.1.15:8000
用方式B(云服务器):改成服务器公网IP,例如 http://47.79.34.220:8000
这一步漏改,或者填的IP和你实际运行后端的地址不一致,App打包出来后会一直显示"连接失败"。
快速开始
# 1. 后端
cd backend
pip install -r requirements.txt
cp .env.example .env    # 然后编辑.env,填好你的API Key
uvicorn server:app --host 0.0.0.0 --port 8000

# 2. App
cd app
npm install
npx expo start
手机装 Expo Go 扫码预览;确认没问题后用 eas build -p android --profile preview 打包正式APK。
关于语音功能
backend/tts.py(语音合成)和 backend/stt.py(语音识别)里的接口地址、模型名是按某个平台的通用格式写的占位实现,不保证和你选择的平台完全一致,使用前请对照你所选平台的官方文档核对、调整。
! 关于依赖版本兼容性
这个项目基于Expo生态,版本兼容性问题是搭建过程中最容易卡住的地方,务必注意:
Expo SDK版本必须和手机上的Expo Go App版本匹配。如果扫码提示"Project is incompatible with this version of Expo Go",说明app/package.json里的expo版本和你手机Expo Go的版本对不上,运行以下命令让项目自动升级到匹配版本:
npx expo install expo@latest
npx expo install --fix
不要用npm install 包名手动装Expo相关的包,一律用npx expo install 包名代替——这样会自动选择跟你当前Expo SDK兼容的版本,手动装很容易装到不兼容的版本,导致"Cannot find native module"这类报错。
expo-av已被官方废弃,新版本Expo(SDK 52+)已经不再支持,语音录制/播放请使用expo-audio。本项目的ChatScreen.js已经用的是新版API,如果你参考网上其他教程用了expo-av的旧写法,记得替换。
装依赖时如果看到大量npm warn deprecated或者Could not resolve dependency,多数是无害的警告,可以忽略;但如果看到npm error ERESOLVE并且安装直接失败,可以加--legacy-peer-deps参数强制跳过版本冲突检查:
npm install --legacy-peer-deps
改动涉及"原生模块"的功能(拍照、录音、推送通知等)后,必须重新执行eas build打包新APK才会生效,不能靠eas update这种远程更新方式推送——OTA更新只能覆盖纯JS代码的改动。
关于人设
backend/persona.py 里的人设是示例内容,仅供参考自己改写,不构成对任何第三方角色/IP的代表或授权声明。如果你改成其他角色的人设,请自行注意相关版权问题,不建议用于商业用途。
