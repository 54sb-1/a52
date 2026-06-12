import os
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.nn.parallel import DistributedDataParallel as DDP
import time

def main():
    # 1. 初始化 DDP 分布式环境
    dist.init_process_group("nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank) # 若无GPU可改用CPU后端 "gloo"

    # 2. 准备数据 (使用 DistributedSampler 确保每个 Pod 分到不同的数据)
    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
    sampler = torch.utils.data.distributed.DistributedSampler(dataset)
    loader = torch.utils.data.DataLoader(dataset, batch_size=64, sampler=sampler)

    # 3. 定义简单 CNN 模型并包装为 DDP
    model = nn.Sequential(
        nn.Conv2d(1, 32, 3, 1), nn.ReLU(),
        nn.Conv2d(32, 64, 3, 1), nn.ReLU(),
        nn.MaxPool2d(2), nn.Flatten(),
        nn.Linear(9216, 128), nn.ReLU(), nn.Linear(128, 10)
    ).to(local_rank)
    
    model = DDP(model, device_ids=[local_rank])
    optimizer = optim.Adadelta(model.parameters(), lr=1.0)

    # 4. 训练计时
    start_time = time.time()
    model.train()
    for epoch in range(1, 3):  # 训练 2 个 epoch
        sampler.set_epoch(epoch)
        for batch_idx, (data, target) in enumerate(loader):
            data, target = data.to(local_rank), target.to(local_rank)
            optimizer.zero_grad()
            output = model(data)
            loss = nn.CrossEntropyLoss()(output, target)
            loss.backward()
            optimizer.step()
            
    if dist.get_rank() == 0:
        print(f"训练完成！总耗时: {time.time() - start_time:.2f} 秒")
    dist.destroy_process_group()

if __name__ == '__main__':
    main()