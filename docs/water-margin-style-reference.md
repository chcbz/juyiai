# Water Margin Style Reference

## Source

- Work: `水浒传` / `水滸傳`
- Public-domain reference checked: Wikisource, `https://zh.wikisource.org/wiki/水滸傳_(120回本)`
- Intended local corpus path when network DNS is available: `docs/reference/water-margin-120.txt`

The current shell environment cannot resolve `zh.wikisource.org`, so the full text was not downloaded in this pass. Use a source with explicit public-domain status and keep the raw corpus under `docs/reference/` rather than `web/src/`, so it is not bundled into frontend assets.

Suggested retrieval command when DNS works:

```bash
mkdir -p docs/reference
curl -L 'https://zh.wikisource.org/wiki/Special:Export/水滸傳_(120回本)' -o docs/reference/water-margin-120.xml
```

## UI Copy Rules

- Prefer compact, scene-bound phrases: `请上梁山`, `山寨安顿`, `自家接应`, `点将`, `领令`.
- Prefer Water Margin social words over technical words: `豪杰`, `头领`, `入伙`, `接应`, `安顿`, `榜文`, `案卷`, `传令`, `回话`.
- Avoid modern infrastructure terms in visible buttons: `绑定`, `接入类型`, `服务器`, `本机配置`, `任务`, `资料检索`.
- Keep operational meaning clear. Use literary labels for visible text, but keep code events and API modes as `server` and `local`.
- Toasts should read like hall notices, not system errors: `请贤未成`, `已在山寨安顿`.

## Current Juyi Hall Lexicon

| Product term | Hall-facing copy |
| --- | --- |
| task / bounty | 榜文 / 悬赏榜文 |
| assign | 点将 / 领令 |
| archive | 收入案卷 |
| public chat | 厅前公议 |
| private chat | 密议 |
| send message | 传令 |
| sync / refresh | 点验 / 重查 |
| library search | 藏书查卷 |
| user/system | 寨中来客 / 传令牌 |
| online/busy/error | 候令 / 办事 / 失联 |
