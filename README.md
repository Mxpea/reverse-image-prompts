# reverse-image-prompts · 通用图像反推

将参考图片中的**视觉规则**反推成可复用的自然语言生图提示词，重点支持“不上传画风参考图”的纯提示词转换。

## 能做什么

- 拆解轮廓、比例、结构连接、线条、色块、阴影与细节密度。
- 区分目标风格不变量、主体身份变量与偶然的截图内容。
- 编写可独立表达目标画风的通用提示词，而不是依赖“像参考图那样”。
- 用户授权后，以真实生成结果迭代，区分已验证版本、文字修订与失败请求。
- 限定实测输入、预算和重试；不把双参考成功当作纯提示词成功。

本 skill 不保证恢复原始提示词或像素级复刻。单个样例成功也不等于所有角色、所有模型都有效。

## 安装

需要 Python 3.10 或更新版本。安装和本地检查均不需要第三方 Python 包，不连接网络、不调用生图 API，也不需要密钥。

在仓库根目录运行：

```powershell
python scripts/install.py
```

默认复制到 `$CODEX_HOME/skills/reverse-image-prompts`；未设置 `CODEX_HOME` 时使用 `~/.codex/skills/reverse-image-prompts`。

先预览，不实际安装：

```powershell
python scripts/install.py --dry-run
```

自定义**技能父目录**：

```powershell
python scripts/install.py --dest "D:/my-codex/skills"
```

上例会安装到 `D:/my-codex/skills/reverse-image-prompts`，不是直接把文件散落在父目录。

macOS／Linux 可将命令中的 `python` 换为 `python3`。安装器拒绝覆盖已存在的同名目录，不修改其他技能、不设置环境变量、不保存 API 凭据。需要更新时，先自行备份并移走原目录，再重新安装；仓库没有隐藏的强制覆盖或卸载操作。

安装完成后可在下一轮对话中使用 `$reverse-image-prompts`；若客户端未刷新技能列表，重新打开会话。

## 使用示例

```text
使用 $reverse-image-prompts 分析这张参考图，写成能把不同人物转换为该画法的通用提示词。
生成时只允许上传待转换人物图，不上传画风参考。先写提示词，不要调用付费 API。
```

若确实要验证，可额外明确：

```text
请继续实测，沿用我指定的模型，本轮最多两次生成请求。
检查实际上传内容，不要把参考图或以前的风格化结果暗中加入输入。
```

技能不会因安装而自动生图。图像执行能力、模型权限与费用仍由使用环境和用户授权决定。

## 仓库结构

```text
reverse-image-prompts/
├── README.md
├── skills/
│   └── reverse-image-prompts/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
│           ├── visual-grammar.md
│           └── validation.md
├── scripts/
│   ├── install.py
│   ├── validate.py
│   └── package.py
└── tests/
    └── test_repository.py
```

`skills/reverse-image-prompts` 是独立的技能安装单元。安装器只复制该目录，不把仓库说明、测试脚本或 Git 元数据装入技能目录。今后发布到 Git 托管服务时，应以这个子目录作为技能路径；本地仓库尚不对应任何已发布的远程地址。

## 检查与打包

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/package.py
```

打包结果为 `dist/reverse-image-prompts.zip`，其中包含可独立安装的完整仓库，不包含 `.git`、缓存或环境文件。解压后进入顶层目录，执行同样的安装命令。

检查覆盖文件结构、UTF-8、技能元数据、相对引用和常见密钥格式；测试覆盖隔离安装、预览、重复安装保护与自定义目录。它们不等价于真实模型出图、跨角色稳定性或完整安全审计。
