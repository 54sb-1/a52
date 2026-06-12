import pandas as pd
import time

print("=== 开始 Pandas 单机性能测试 ===")
start_time = time.time()

# 1. 读取数据 (在你的本地或云端环境执行)
# 注意：云端测试时，需要先将 OBS 里的 CSV 下载到云服务器本地路径
df = pd.read_csv("douban.csv")

# 2. 数据清洗
df_clean = df.dropna(subset=['title', 'rating'])
df_clean['genre'] = df_clean['genre'].fillna('未知')

# 3. 核心统计：GROUP BY 聚合
# 计算各类型的平均分和数量
genre_stats = df_clean.groupby('genre').agg(
    avg_rating=('rating', 'mean'),
    movie_count=('title', 'count') # 使用 title 列计数
).reset_index()

# 过滤数量 > 10 并按评分降序排列
result = genre_stats[genre_stats['movie_count'] > 10].sort_values(by='avg_rating', ascending=False)

print(result.head(5))

# 4. 记录单机总耗时
end_time = time.time()
print(f"\n✅ Pandas 单机总耗时: {end_time - start_time:.2f} 秒")