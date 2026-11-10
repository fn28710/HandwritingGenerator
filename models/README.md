此目录存放风格模型的输出文件夹。

约定：每个子目录 = 一个风格模型。
模型结构：models/<模型名>/
  style.json    全局风格参数
  manifest.csv  字符映射
  variants/     每字符的字图索引
  info.json     模型元信息（含 dataset 字段，固定对应一个数据集）
