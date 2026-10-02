# 清算后端

Python 3.11+ 标准库 HTTP API + SQLite，无需安装第三方包。负责输入校验、递归下降表达式解析、计算和历史持久化；前端仅发送表达式。

## 运行

在本仓库目录运行 `python src/server.py`，默认地址 http://localhost:8000。首次启动自动创建 `data/history.sqlite3` 和 history 表。

配置环境变量：`HOST`（默认 127.0.0.1）、`PORT`（8000）、`CALCULATOR_DB`（data/history.sqlite3）、`FRONTEND_ORIGIN`（http://localhost:5500）。实际前端访问地址必须与允许的来源一致。

测试：`python -m unittest discover -s tests -v`。测试使用临时数据库，验证表达式、错误输入、API、重启持久化、删除和分页。

## API

| 方法 | 地址 | 用途 |
|---|---|---|
| POST | /api/calculate | JSON 对象 `{"expression":"(1+2)*3"}` |
| GET | /api/history?page=1&q= | 每页 10 条，按表达式子串搜索 |
| DELETE | /api/history/{id} | 删除指定记录 |
| GET | /api/health | 服务存活检查 |

成功计算返回 201 和 success、id、expression、result、created_at。result 为十进制字符串，避免 JSON 浮点精度损失；时间为 UTC ISO 8601。无效输入返回 400，不存在的记录或接口返回 404，数据库错误返回 500。

表达式支持 + - * / × ÷、括号、一元正负、小数。最多 500 字符、嵌套 64 层，运算有效位数 28 位，循环小数按此精度舍入。不支持隐式乘法、科学计数法、函数或幂运算。不使用 eval/exec。

## 部署

免费托管方案见 [免费部署.md](免费部署.md)。`src/wsgi.py` 是 WSGI 入口，与本地 HTTP 服务复用同一套接口和数据库逻辑，无新增第三方依赖。

可在 Linux 服务器用 Python 启动并交由进程管理器常驻，配置 Nginx HTTPS 反向代理。只将代理端口暴露公网，后端监听 127.0.0.1；数据库路径设置为持久目录并定期备份。此版本为课程演示服务，历史为所有访客共享，无用户登录，任何访客均可删除演示记录。公网环境需由反向代理配置请求速率和请求大小限制。数据库不可放在静态前端目录。
