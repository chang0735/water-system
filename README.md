# 水站管理系统 (Water Station Management System)

> GitHub: https://github.com/chang0735/water-system
> 生产地址: https://water-system-production.up.railway.app/

## 账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 销售（订单/客户/产品/统计） |
| cangguan | warehouse123 | 仓管（订单/统计） |
| songshui | delivery123 | 送水工（订单/统计） |

## 技术栈

- 前端: 单文件 SPA (vanilla JS, index.html)
- 后端: Flask (app.py)
- 数据库: SQLite (data/water.db)
- 部署: Railway (自动从 GitHub main 分支部署)

## 已完成的优化（2024-06-24）

### Bug 修复
- API 路径: /stats /products /customers → /api/stats /api/products /api/customers
- 移除 jQuery 依赖，全部改为原生 JS
- 修复状态栏点击切换（之前用了未加载的 jQuery $()）
- 数据库从 /tmp 移到 data/ 目录，防止重启丢失
- 订单创建兼容 customerName 和 customer_name

### 安全
- XSS 防护: escapeHtml() 转义所有用户数据
- 输入校验: 手机号正则、必填项、价格范围

### UX 优化
- Toast 通知系统（成功/失败/警告/消息）
- Loading 动画（所有页面加载时）
- 400ms 防抖搜索
- 模态表单替代 prompt() 弹窗
- 登录 localStorage 持久化
- 操作确认对话框
- 粘性顶栏导航
- 已取消订单筛选

### 客户-订单联动
- 新建订单可选择已有客户（下拉框）
- 选中客户自动填入电话、地址
- 订单内可快速新增客户，保存后自动选中
- 客户管理页支持删除
- populateCustomerSelect() 统一刷新下拉框

## 本地运行

```bash
cd D:\claude code\water-system
pip install flask
python app.py
# 访问 http://localhost:5000
```

## 部署

推送到 GitHub main 分支，Railway 自动部署。
