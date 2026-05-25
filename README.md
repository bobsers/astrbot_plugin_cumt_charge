# CUMT 充电口查询插件

把整个 `asbot_plugin_cumtcharge` 目录放进 `AstrBot/data/plugins/`，安装依赖后重载插件即可。

## 指令

- `/charge <suid>`
  - 查询当前是否有空余充电口。
  - 优先按 `online=1 && charge_status=0` 判断。
  - 如果接口没有明确给出空闲口，但存在 `功率≈0、电流≈0、时长=0、电量=0` 的端口，会提示“疑似空闲”。
  - 也支持传站点名称正则；会在监听列表缓存的站点名里做匹配。

- `/charge <suid> <端口号>`
  - 返回对应端口的详细信息。
  - 端口号按 `1号口、2号口...` 这种自然编号传入。

- `/chargeall <suid>`
  - 不再直接回原始 JSON。
  - 会把两个接口的结果按字段翻译后拆分。
  - 每个充电口单独一条节点消息。
  - 群聊里会优先按合并转发发送。
  - 如果单个合并转发过大，会自动拆成多组合并转发发送。
  - 如果不是群聊，则回退为分段发送。
  - 只支持直接传 `suid`，不支持站点名称映射。

## 当前实现说明

- `token` 当前硬编码在 [main.py](./main.py) 里。
- 详情接口：`https://api.powerliber.com/client/1/device/detail`
- 端口状态接口：`https://power-api.powerliber.com/client/2/device/profile`
