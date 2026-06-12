# CloudShell执行，先上传QQ群里面的离线压缩包到OBS，并解压出 ./spark-operator-chart/ 目录
# 在./spark-operator-chart/ 父目录执行
# 在新命名空间spark-operator创建spark-operator，名为spark-op
helm install spark-op ./spark-operator-chart/ -n spark-operator --create-namespace
# 查看 Operator 状态，需要 STATUS 变为 Running
kubectl get pods -n spark-operator -w  

# 预热测试，执行 WordCount 示例 (B-1)
kubectl apply -f sparkapplication-1.yaml

# 查看 Pod 状态（Driver 和 Executor 被拉起）
kubectl get pods -n default -w 

kubectl logs -f spark-wordcount-driver  #-f表示实时跟踪
# 截图，看到 "Top 10 words" 输出。


# 先 douban.csv 和 analysis.py 上传至 OBS 桶
kubectl apply -f sparkapplication-2.yaml

# 查看 Pod 状态，需要看到RUNNING
kubectl get pods -n default -w 

# 查看分析结果
kubectl logs -f pyspark-douban-analysis-driver
# 截图，看到 analysis.py 里的各阶段打印结果（Schema、缺失值、以及4个SQL查询表格）。