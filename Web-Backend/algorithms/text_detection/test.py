import argparse
import os
import subprocess
from transformers import *
from transformers import AutoTokenizer, AutoModelForMaskedLM
import sys
import numpy as np
from itertools import count
from multiprocessing import Process
from sklearn.metrics import roc_auc_score
import torch
import torch.distributed as dist
from torch import nn
import torch.nn.functional as F
from torch.nn.parallel import DistributedDataParallel
from torch.optim import Adam
from torch.utils.data import DataLoader, DistributedSampler, RandomSampler
from tqdm import tqdm
import multiprocessing
import pandas as pd
import time
import csv
import sys
from functools import reduce
from torch.utils.data import Dataset

from torch import nn
import torch.distributed as dist


def summary(model: nn.Module, file=sys.stdout):
    def repr(model):
        # We treat the extra repr like the sub-module, one item per line
        extra_lines = []
        extra_repr = model.extra_repr()
        # empty string will be split into list ['']
        if extra_repr:
            extra_lines = extra_repr.split('\n')
        child_lines = []
        total_params = 0
        for key, module in model._modules.items():
            mod_str, num_params = repr(module)
            mod_str = nn.modules.module._addindent(mod_str, 2)
            child_lines.append('(' + key + '): ' + mod_str)
            total_params += num_params
        lines = extra_lines + child_lines

        for name, p in model._parameters.items():
            if hasattr(p, 'shape'):
                total_params += reduce(lambda x, y: x * y, p.shape)

        main_str = model._get_name() + '('
        if lines:
            # simple one-liner info, which most builtin Modules will use
            if len(extra_lines) == 1 and not child_lines:
                main_str += extra_lines[0]
            else:
                main_str += '\n  ' + '\n  '.join(lines) + '\n'

        main_str += ')'
        if file is sys.stdout:
            main_str += ', \033[92m{:,}\033[0m params'.format(total_params)
        else:
            main_str += ', {:,} params'.format(total_params)
        return main_str, total_params

    string, count = repr(model)
    if file is not None:
        if isinstance(file, str):
            file = open(file, 'w')
        print(string, file=file)
        file.flush()

    return count


def grad_norm(model: nn.Module):
    total_norm = 0
    for p in model.parameters():
        param_norm = p.grad.data.norm(2)
        total_norm += param_norm.item() ** 2
    return total_norm ** 0.5

def distributed():
    print(dist.is_available() and dist.is_initialized())
    return dist.is_available() and dist.is_initialized()


def setup_distributed(port=29500):
    if not dist.is_available() or not torch.cuda.is_available() or torch.cuda.device_count() <= 1:
        print("single gpu")
        return 0, 1

    if 'MPIR_CVAR_CH3_INTERFACE_HOSTNAME' in os.environ:
        from mpi4py import MPI
        mpi_rank = MPI.COMM_WORLD.Get_rank()
        mpi_size = MPI.COMM_WORLD.Get_size()

        os.environ["MASTER_ADDR"] = '127.0.0.1'
        os.environ["MASTER_PORT"] = str(port)

        dist.init_process_group(backend="nccl", world_size=mpi_size, rank=mpi_rank)
        return mpi_rank, mpi_size

    dist.init_process_group(backend="nccl", init_method="env://")
    return dist.get_rank(), dist.get_world_size()

def load_rumordata(data_file, expected_size=None):
    texts = []
    label=[]
    with open(data_file) as csvfile:
        csv_reader=csv.reader(csvfile,delimiter='\t')
        for row in csv_reader:
            # print(row)
            texts.append(row[0])
            label.append(int(row[1]))
    return texts,label

class Corpus:
    def __init__(self, name, skip_train=False,minichange_test=False,k=1):
        self.name = name
        # 加载数据集
        if  self.name=='rumor':
            self.test_texts,self.test_label = load_rumordata(f'rumor_data/rumor_eval_list.csv', expected_size=424)

class EncodedDataset(Dataset):
    def __init__(self, corpus: dict, tokenizer: PreTrainedTokenizer,
                 max_sequence_length: int = None, min_sequence_length: int = None, epoch_size: int = None,
                 token_dropout: float = None, seed: int = None):
        self.corpus = corpus # dict,含有texts和label
        self.texts=corpus['texts'] # list
        self.label=corpus['label'] # list
        self.tokenizer = tokenizer
        self.max_sequence_length = max_sequence_length
        self.min_sequence_length = min_sequence_length
        self.epoch_size = epoch_size
        self.token_dropout = token_dropout
        self.random = np.random.RandomState(seed)

    def __len__(self):
        return self.epoch_size or len(self.texts)
    def __getitem__(self, index):
        # 根据索引 index 获取数据集中的单个样本
        text = self.texts[index]
        label = self.label[index]

        # 使用 tokenizer 对文本进行编码
        tokens = self.tokenizer.encode(text, add_special_tokens=True)

        if self.max_sequence_length is not None:
            tokens = tokens[:self.max_sequence_length]

            if self.min_sequence_length:
                output_length = self.random.randint(min(self.min_sequence_length, len(tokens)), len(tokens) + 1)
                start_index = 0 if len(tokens) <= output_length else self.random.randint(0, len(tokens) - output_length + 1)
                end_index = start_index + output_length
                tokens = tokens[start_index:end_index]

        if self.token_dropout:
            dropout_mask = self.random.binomial(1, self.token_dropout, len(tokens)).astype(np.bool)
            tokens = np.array(tokens)
            tokens[dropout_mask] = self.tokenizer.unk_token_id
            tokens = tokens.tolist()

        # 将 tokens 转换为 PyTorch 张量
        tokens = torch.tensor(tokens)
        
        if self.max_sequence_length is None or len(tokens) == self.max_sequence_length:
            mask = torch.ones(len(tokens))
            return tokens, mask, label

        # 如果长度不满足 max_sequence_length，则进行填充
        padding_length = self.max_sequence_length - len(tokens)
        padding = torch.full((padding_length,), self.tokenizer.pad_token_id)
        tokens = torch.cat([tokens, padding])
        mask = torch.cat([torch.ones(len(tokens) - padding_length), torch.zeros(padding_length)])

        return tokens, mask, label

def load_datasets(dataset_name,  tokenizer, batch_size,
                  max_sequence_length, random_sequence_length, epoch_size=None, token_dropout=None, seed=None):
   
    corpus = Corpus(dataset_name)
    # 获取文本和标签
    test_text=corpus.test_texts
    test_label=corpus.test_label
    test=dict()
    test['texts']=test_text
    test['label']=test_label
    
    Sampler = DistributedSampler if distributed() and dist.get_world_size() > 1 else RandomSampler

    min_sequence_length = 10 if random_sequence_length else None

    test_dataset = EncodedDataset(test, tokenizer)
    test_loader = DataLoader(test_dataset, batch_size=1, sampler=Sampler(test_dataset))
    return test_loader


def accuracy_sum(logits, labels):
    if list(logits.shape) == list(labels.shape) + [2]:
        # 2-d outputs
        classification = (logits[..., 0] < logits[..., 1]).long().flatten()
    else:
        classification = (logits > 0).long().flatten()
    assert classification.shape == labels.shape
    return (classification == labels).float().sum().item()

# 返回TP,FP,FN
def precision_sum(logits, labels):
    if list(logits.shape) == list(labels.shape) + [2]:
        # 2-d outputs
        classification = (logits[..., 0] < logits[..., 1]).long().flatten()
    else:
        classification = (logits > 0).long().flatten()
    assert classification.shape == labels.shape
    return (classification == labels == 1).float().sum().item(),(classification ==1 and labels == 0).float().sum().item(),(classification ==0 and labels == 1).float().sum().item()

def validate(model: nn.Module, device: str, loader: DataLoader, votes=1, desc='Validation'):
    model.eval()

    validation_accuracy = 0
    validation_epoch_size = 0
    validation_loss = 0
    TP=0
    FP=0
    FN=0
    

    y_labels = []
    y_labels_pred = []
    records = [record for v in range(votes) for record in tqdm(loader, desc=f'Preloading data ... {v}',
                                                               disable=False)]
    records = [[records[v * len(loader) + i] for v in range(votes)] for i in range(len(loader))]
    print("start validate")
    with tqdm(records, desc=desc, disable=distributed() and dist.get_rank() > 0) as loop, torch.no_grad():
        for example in loop:
            losses = []
            logit_votes = []


            for texts, masks, labels in example:
                texts, masks, labels = texts.to(device), masks.to(device), labels.to(device)
                batch_size = texts.shape[0]

                outputs = model(texts, attention_mask=masks, labels=labels)
                loss = outputs.loss
                logits = outputs.logits
                y_labels.append(labels)
                y_labels_pred.append(F.sigmoid(logits)[0][1])
                losses.append(loss)
                logit_votes.append(logits)

            loss = torch.stack(losses).mean(dim=0)
            logits = torch.stack(logit_votes).mean(dim=0)
            
            

            batch_accuracy = accuracy_sum(logits, labels)
            TP_t,FP_t,FN_t = precision_sum(logits, labels)
            TP += TP_t
            FP += FP_t
            FN += FN_t
            validation_accuracy += batch_accuracy
            validation_epoch_size += batch_size
            validation_loss += loss.item() * batch_size


            loop.set_postfix(loss=loss.item(), acc=validation_accuracy / validation_epoch_size)
    return {
        "validation/accuracy": validation_accuracy,
        "validation/epoch_size": validation_epoch_size,
        "validation/loss": validation_loss,
        "validation/TP": TP,
        "validation/FP": FP,
        "validation/FN":FN,
        "validation/pro":torch.tensor(y_labels_pred),
        "validation/labels":torch.tensor(y_labels)
    }

def safe_div(a,b):
    if a == 0 and b == 0:
        return 1
    else:
        return a+b

def _all_reduce_dict(d, device):
    # wrap in tensor and use reduce to gpu0 tensor
    output_d = {}
    for (key, value) in sorted(d.items()):
        if key != "validation/labels" and key != "validation/pro":
            tensor_input = torch.tensor([[value]]).to(device)
            torch.distributed.all_reduce(tensor_input)
            output_d[key] = tensor_input.item()
        else:
            # 处理 "validation/labels" 和 "validation/pro" 的键值对
            # 将值包装成张量，将张量移动到指定的设备
            tensor_input = torch.tensor(value).to(device)
            
            # 对张量进行分布式拼接而非求和
            all_tensors = [torch.zeros_like(tensor_input) for _ in range(torch.distributed.get_world_size())]
            torch.distributed.all_gather(all_tensors, tensor_input)
            
            # 在主 GPU（rank=0）上进行拼接
            if torch.distributed.get_rank() == 0:
                # print("主gpu拼接")
                concatenated_tensor = torch.cat(all_tensors, dim=0)
                output_d[key] = concatenated_tensor.tolist()
    return output_d

def run(max_epochs=None,
        device=None,
        batch_size=24,
        max_sequence_length=256,
        random_sequence_length=False,
        epoch_size=None,
        seed=None,
        dataset_name='rumor',
        token_dropout=None,
        learning_rate=3e-5,
        weight_decay=0,
        **kwargs):
    args = locals()
    rank, world_size = setup_distributed()

    if device is None:
        device = f'cuda:{rank}' if torch.cuda.is_available() else 'cpu'

    print('rank:', rank, 'world_size:', world_size, 'device:', device)

    import torch.distributed as dist
    if distributed() and rank > 0:
        dist.barrier()
    
    model_name='chinese-roberta-wwm-ext'
    tokenization_utils.logger.setLevel('ERROR')
    
    tokenizer = AutoTokenizer.from_pretrained("chinese-roberta-wwm-ext")
    model = RobertaForSequenceClassification.from_pretrained("chinese-roberta-wwm-ext")
    # 将模型移动到 GPU
    model = model.to(device)
    print("model load success")
    if rank == 0:
        summary(model)
        if distributed():
            dist.barrier()

    if world_size > 1:
        # model = DistributedDataParallel(model, [rank], output_device=rank, find_unused_parameters=True)
        model = DistributedDataParallel(model)
   
    test_loader = load_datasets(dataset_name,  tokenizer, batch_size,
                                                        max_sequence_length, random_sequence_length, epoch_size,
                                                        token_dropout, seed)

    
    

    modeldir = os.environ.get("OPENAI_LOGDIR", f"models_{dataset_name}_{learning_rate}_{batch_size}_decay")
    # print(f"进程{rank}加载效果最好模型....")
    print("load best model")
    try:
        checkpoint = torch.load(os.path.join("model","best-model.bin"))
            # print("checkpoint",checkpoint)
            # print("model param",{k.replace('module.', ''): v for k, v in checkpoint.items()})
        model.load_state_dict({k.replace('module.', ''): v for k, v in checkpoint.items()})
    except Exception as e:
        print("模型加载错误，重新加载....",e)
        time.sleep(5000)
        model.load_state_dict(torch.load(os.path.join(modeldir, "best-model.bin"), map_location=device))
        
        
    print("load best model success")    
    test_alone_metrics = validate(model, device, test_loader)
    print(f"进程{rank}测试完成")
    # print(f"开始进行指标合并！{rank}")
    # 指标合并
    if distributed():
        test_metrics = _all_reduce_dict({**test_alone_metrics},device)
    else:
        test_metrics = test_alone_metrics
    # print(f"进程{rank}指标合并完成")
    # 合并后计算指标
    if rank==0:
        test_metrics['validation/accuracy'] /= test_metrics['validation/epoch_size']
        precision=test_metrics['validation/TP']/safe_div(test_metrics['validation/TP'],test_metrics['validation/FP'])
        recall=test_metrics['validation/TP']/safe_div(test_metrics['validation/TP'],test_metrics['validation/FN'])
        F1=2*precision*recall/safe_div(precision,recall)
        test_metrics['validation/loss'] /= test_metrics['validation/epoch_size']
        print('acc:\t',test_metrics['validation/accuracy'])
        print('precision:\t',precision)
        print('recall:\t',recall)
        print('F1:\t',F1)
        probabilities_np = np.array(test_metrics['validation/pro'])
        labels_np = np.array(test_metrics['validation/labels'])
        auc = roc_auc_score(labels_np, probabilities_np)
        print(f'AUC: {auc}')
        print('执行完成!')
        return {
            'acc':test_metrics['validation/accuracy'],
            'precision:':precision,
            'recall:':recall,
            'AUC':auc,
            'F1':F1
        }

if __name__ == '__main__':
    os.environ["CUDA_VISIBLE_DEVICES"] = "5,2"
    parser = argparse.ArgumentParser()

    parser.add_argument('--max-epochs', type=int, default=50)
    parser.add_argument('--device', type=str, default=None)
    parser.add_argument('--batch-size', type=int, default=32)#10
    parser.add_argument('--max-sequence-length', type=int, default=256)
    parser.add_argument('--random-sequence-length', action='store_true')
    parser.add_argument('--epoch-size', type=int, default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--dataset_name', type=str, default='rumor')
    parser.add_argument('--token-dropout', type=float, default=None)
    parser.add_argument('--learning-rate', type=float, default=3e-5)#3e-6
    parser.add_argument('--weight-decay', type=float, default=0)
    args = parser.parse_args()
    # 设置启动方法为 'spawn'
    multiprocessing.set_start_method('spawn')
    nproc = int(subprocess.check_output([sys.executable, '-c', "import torch;"
                                         "print(torch.cuda.device_count() if torch.cuda.is_available() else 1)"]))
    print("可用进程数:{}".format(nproc))
    if nproc > 1:
        print(f'Launching {nproc} processes ...', file=sys.stderr)

        os.environ["MASTER_ADDR"] = '127.0.0.1'
        os.environ["MASTER_PORT"] = str(29500)
        os.environ['WORLD_SIZE'] = str(nproc)
        os.environ['OMP_NUM_THREAD'] = str(1)
        subprocesses = []

        for i in range(nproc):
            os.environ['RANK'] = str(i)
            os.environ['LOCAL_RANK'] = str(i)
            process = Process(target=run, kwargs=vars(args))
            process.start()
            subprocesses.append(process)

        for process in subprocesses:
            process.join()
    else:
        run(**vars(args))