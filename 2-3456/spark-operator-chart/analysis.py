from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, isnan, desc, avg
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
import time

start_time = time.time()

spark = SparkSession.builder.appName("DoubanCloudAnalysis").getOrCreate()

print("==========================================")
print("       A-1. 数据清洗阶段开始              ")
print("==========================================")

# ⚠️ 注意：这里的 s3a:// 路径需要替换为教师在群里公布的真实 OBS Bucket 路径
obs_data_path = "s3a://<TEACHER_BUCKET>/douban.csv" 
df = spark.read.csv(obs_data_path, header=True, inferSchema=True)

print("1. 原始数据 Schema 和前 5 行:")
df.printSchema()
df.show(5)

print("2. 统计各字段缺失值比例:")
total_count = df.count()
missing_stats = df.select([(count(when(isnan(c) | col(c).isNull(), c)) / total_count).alias(c) for c in df.columns])
missing_stats.show()

print(f"清洗前总行数: {total_count}")

# 策略1：关键字段 (title, rating) 缺失直接丢弃 (dropna)
# 原因：电影名和评分是后续统计的核心，缺失这部分数据无法进行有效插值，会严重干扰 Top-N 和均值计算。
df_clean = df.dropna(subset=["title", "rating"])

# 策略2：非关键辅助字段 (如 genre 类型) 缺失进行填充 (fillna)
# 原因：类型缺失不影响其作为独立个体的评分，将其归为"未知"类可以保留样本容量。
if "genre" in df_clean.columns:
    df_clean = df_clean.fillna({"genre": "未知"})

clean_count = df_clean.count()
print(f"清洗后总行数: {clean_count}")
print(f"剔除无效数据: {total_count - clean_count} 行")


print("\n==========================================")
print("       A-2. Spark SQL 统计分析阶段        ")
print("==========================================")
df_clean.createOrReplaceTempView("movies")

print("查询 1：[GROUP BY 聚合] - 各类型电影的平均评分与数量")
q1 = spark.sql("""
    SELECT genre, ROUND(AVG(rating), 2) as avg_rating, COUNT(1) as movie_count 
    FROM movies 
    GROUP BY genre 
    HAVING movie_count > 10 
    ORDER BY avg_rating DESC
""")
q1.show(5)

print("查询 2：[ORDER BY Top-N] - 历史评分最高的 Top 10 神作")
q2 = spark.sql("""
    SELECT title, rating, year, genre 
    FROM movies 
    ORDER BY rating DESC 
    LIMIT 10
""")
q2.show()

print("查询 3：[时间维度趋势] - 近20年每年发行的电影数量趋势")
q3 = spark.sql("""
    SELECT year, COUNT(1) as release_count 
    FROM movies 
    WHERE year >= 2000 
    GROUP BY year 
    ORDER BY year DESC
""")
q3.show(5)

print("查询 4：[窗口函数] - 取出每年评分排名第一的年度最佳电影")
q4 = spark.sql("""
    SELECT year, title, rating FROM (
        SELECT year, title, rating, 
        ROW_NUMBER() OVER(PARTITION BY year ORDER BY rating DESC) as rk
        FROM movies
    ) tmp 
    WHERE rk = 1 AND year >= 2010
    ORDER BY year DESC
""")
q4.show(5)

print(f"\n分布式计算总耗时: {time.time() - start_time:.2f} 秒")
spark.stop()