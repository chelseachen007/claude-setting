# Layer 3：缓存/镜像搜索

Layer 1 + Layer 2 都失败时的最终降级手段。

## 策略（按顺序尝试）

1. **Google 缓存**：用 WebSearch 搜索 `cache:{原始URL}`
2. **网页存档**：
   - `https://webcache.googleusercontent.com/search?q=cache:{URL}`
   - `https://web.archive.org/web/*/{URL}`
3. **内容聚合搜索**：用 WebSearch 搜索文章标题关键词，查找转载/镜像版本
4. **Jina Reader**：`https://r.jina.ai/{URL}` 作为最后的静态提取尝试

## 全部失败

如果三层策略全部失败，**立即**明确告知用户：

> 无法从该 URL 提取内容（原因：[具体失败原因]）。请手动打开链接，复制正文内容粘贴给我，我会帮你处理。
