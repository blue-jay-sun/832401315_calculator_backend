# 清算课程作业部署版

前端为独立 HTML/CSS/JavaScript，后端提供 HTTP JSON 接口。保留 Python 本地版，此目录是兼容 Sites 的部署适配版。

- API：POST /api/calculate、GET /api/history?page=1&q=、DELETE /api/history/{id}、GET /api/health。
- 数据：D1 SQLite 持久数据库，参数化查询；成功计算写入表达式、结果、UTC 时间。
- 计算：递归下降语法 + BigInt 有理数运算，最后按 28 位有效数字、半偶规则舍入；与 Python Decimal 每步舍入略有差异。支持四则运算、括号、一元正负、小数，禁止代码执行。最多 500 字符、64 层嵌套。
- 历史为公开演示数据，所有访问者共享，可删除。不要输入个人隐私。
- 验证：合法/非法表达式测试；接口计算、读库、删除、健康检查；生产构建。

Python 原版仓库：https://github.com/blue-jay-sun/832401315_calculator_backend
前端原版仓库：https://github.com/blue-jay-sun/832401315_calculator_frontend
