# Fork 说明（clash-traffic-monitor-plus）

基于上游 [zhf883680/clash-traffic-monitor](https://github.com/zhf883680/clash-traffic-monitor) 的增强版。

## 本 fork 的改动

**功能：走势图点击联动筛选**（2026-10-24，+204/-31 行，仅前端）

- 点击趋势图上某个小时柱 → 主表/副表立即过滤到该时段流量，点空白处还原
- 过滤状态有徽章提示，点徽章一键清除（`clearTrendFilterAndReload` / `syncTrendFilterBadge`）
- 联动刷新只重载表格不整页刷新（`loadTablesOnly`）
- 时间范围/粒度/模式选择写入 localStorage 记忆（`loadStoredGranularity` / `persistSelectedGranularity` / `effectiveRange`）
- 悬停提示与选中态的重绘修正

改动文件：`web/app.js`、`web/index.html`、`web/styles.css`；`patch.py` 为当次修改的补丁脚本（保留作参考）。

详细修改逻辑见 `docs/流量监控-修改报告.md`，使用说明见 `docs/流量监控-使用报告.md`。

## 构建方法

```bash
# 需要 Go 1.21+（当时用便携版 go1.23 windows/amd64 编译）
go build -o traffic-monitor-patched.exe .

# 运行（默认 :18080，数据存 data/ 目录）
./traffic-monitor-patched.exe
```

- exe 为构建产物，已加入 .gitignore，不入库
- mihomo 内核连接配置在 Web 设置里填（API 地址 + secret）
- 替换正在运行的 exe：先停进程再覆盖，数据在 `data/*.db` 不会丢

## 与上游同步

```bash
git remote add upstream https://github.com/zhf883680/clash-traffic-monitor
git fetch upstream && git merge upstream/main
```
