# DATA2001 小组作业


## 当前项目结构
```text
data/
  raw/          # 原始数据
  processed/    # 清洗后的数据
  statistics/   # 统计结果的汇总
docs/           # 作业相关的资源
notebooks/      # 最终用于提交的jupyter notebook
report/         # 最终用于提交的报告
src/
  task1_cleaning/ # task1的数据清洗部分, 每个人完成一个清洗方向
  task1_statistics/ # task1的数据统计部分, 每个人完成5个统计项
```

## 环境配置
```bash
uv sync

source .venv/bin/activate # linux和mac进入虚拟环境
.venv\Scripts\Activate.ps1 # windows powershell 进入虚拟环境

# 有些ide可能还需要手动选择当前虚拟环境作为python解释器

uv add {包名} 
# 如果你需要的包在当前的toml中不存在, 使用uv add 添加依赖
```


## 已有模块的推荐运行方法
```bash
uv run python -m src.task1_cleaning.pipeline # 推荐直接使用uv运行
uv run python -m src.task1_statistics.pipeline

# 建议后续代码中统一使用从src开始的绝对导入
```

## Task 1 Pipeline 设计
没有实现的函数请统一写成, 这样执行的时候可以跳过未实现的函数：
```python
raise NotImplementedError("function_name is not implemented yet")
```


## Notebook 建议
推荐在查看清洗或者统计结果的时候, 优先打开notebook来运行和查看

在 notebook 中展示表格时，优先使用 pandas DataFrame, 效果比csv和纯文本好：
```python
display(df)
```

## Git 使用约定
建议流程：
```bash
git checkout -b '分支名'
git add .
git commit -m "修改内容"
git push origin '分支名'
```
不要直接push到主分支, 需要合并的时候创建pr来合并, 防止污染主分支


## 代表事项
- task1
  - [] 获取原始csv文件
  - [] 各个组员各自src/task1_cleaning/下面选择一个清洗函数完成(有需要的话可以创建更多清洗函数)
  - [] 各个组员各自想出5个个衍生统计数据, 并在src/task1_statistic/下面的自己对应的文件里面实现5个对应的函数
  - [] 完成task1阶段的notebook, 在notebook中导入和调用task1的两个模块, 并展示结果
  - [] 完成task1阶段的报告
