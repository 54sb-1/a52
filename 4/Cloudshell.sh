# 先把QQ群上传到OBS并解压
# 然后在新命名空间monitoring里面安装监控
helm install monitoring ./kube-prometheus-stack-chart/ -n monitoring --create-namespace
#附加题3，训练
kubectl apply -f pytorch_job.yaml
