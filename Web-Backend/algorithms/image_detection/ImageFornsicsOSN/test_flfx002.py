import os
# from uts import get_available_gpu

# gpu_ids = get_available_gpu()
os.environ['CUDA_VISIBLE_DEVICES'] = str(0)

import cv2
import copy
import shutil
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
# import os, sys
# os.chdir(sys.path[0]) #使用文件所在目录
# sys.path.append(os.getcwd()) #添加工作目录到模块搜索目录列表

from sklearn.metrics import roc_auc_score
from .models.scse import SCSEUnet
# from models.scse import SCSEUnet


class MyDataset(Dataset):
    def __init__(self, test_path='', size=896):
        self.test_path = test_path
        self.size = size
        # self.filelist = sorted(os.listdir(self.test_path))
        self.transform = transforms.Compose([
            np.float32,
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])

    def __getitem__(self, idx):
        return self.load_item(idx)

    def __len__(self):
        return 1

    def load_item(self, idx):
        # fname1, fname2 = self.test_path + self.filelist[idx], ''
        fname1 = self.test_path

        img = cv2.imread(fname1)[..., ::-1]
        H, W, _ = img.shape
        mask = np.zeros([H, W, 3])

        H, W, _ = img.shape
        img = img.astype('float') / 255.
        mask = mask.astype('float') / 255.
        return self.transform(img), self.tensor(mask[:, :, :1]), fname1.split('/')[-1]

    def tensor(self, img):
        return torch.from_numpy(img).float().permute(2, 0, 1)


class Detector(nn.Module):
    def __init__(self):
        super(Detector, self).__init__()
        self.name = 'detector'
        self.det_net = SCSEUnet(backbone_arch='senet154', num_channels=3)

    def forward(self, Ii):
        Mo = self.det_net(Ii)
        return Mo


class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.save_dir = 'ImageFornsicsOSN/weights/'
        self.networks = Detector()
        self.gen = nn.DataParallel(self.networks).cuda()

    def forward(self, Ii):
        return self.gen(Ii)

    def load(self, path=''):
        self.gen.load_state_dict(torch.load(self.save_dir + path + '%s_weights.pth' % self.networks.name))


def forensics_test(model, url):
    test_size = '896'
    # test_path = 'data/input/'
    # test_path = 'data/Columbia/'
    test_path = url
    # decompose(test_path, test_size)
    # print('Decomposition complete.')
    # test_dataset = MyDataset(test_path='data/ImageFornsicsOSN/tmp/input_decompose_' + test_size + '/', size=int(test_size))
    test_dataset = MyDataset(test_path=test_path, size=int(test_size))
    # path_out = 'data/ImageFornsicsOSN/tmp/input_decompose_' + test_size + '_pred/' # 'temp/input_decompose_896_pred/'
    test_loader = DataLoader(dataset=test_dataset, batch_size=1, shuffle=False, num_workers=1)
    # rm_and_make_dir(path_out)
    for items in test_loader:
        Ii, Mg = (item.cuda() for item in items[:-1])
        filename = items[-1]
        Mo = model(Ii)
        Mo = Mo * 255.
        Mo = Mo.permute(0, 2, 3, 1).cpu().detach().numpy()
        for i in range(len(Mo)):
            Mo_tmp = Mo[i][..., ::-1]
            # cv2.imwrite(path_out + filename[i][:-4] + '.png', Mo_tmp)
    result = classify_image(Mo_tmp)
    # print('Prediction complete.')
    # if os.path.exists('data/ImageFornsicsOSN/tmp/input_decompose_' + test_size + '/'):
    #     shutil.rmtree('data/ImageFornsicsOSN/tmp/input_decompose_' + test_size + '/')
    # path_pre = merge(test_path, test_size) # 'data/output/'
    # print('Merging complete.')

    # path_gt = 'data/mask/'
    # path_gt = 'ImageFornsicsOSN/data/Columbia_GT/'
    # if os.path.exists(path_gt):
    #     flist = sorted(os.listdir(path_pre))
    #     auc, f1, acc, precision, recall = [], [], [], [], []
    #     for file in flist:
    #         pre = cv2.imread(path_pre + file)
    #         gt = cv2.imread(path_gt + file[:-4] + '_gt.png')
    #         H, W, C = pre.shape
    #         Hg, Wg, C = gt.shape
    #         if H != Hg or W != Wg:
    #             gt = cv2.resize(gt, (W, H))
    #             gt[gt > 127] = 255
    #             gt[gt <= 127] = 0
    #         if np.max(gt) != np.min(gt):
    #             auc.append(roc_auc_score((gt.reshape(H * W * C) / 255).astype('int'), pre.reshape(H * W * C) / 255.))
    #         pre[pre > 127] = 255
    #         pre[pre <= 127] = 0
    #         a, _, c, d, e = metric(pre / 255, gt / 255)
    #         f1.append(a)
    #         # iou.append(b)
    #         acc.append(c)
    #         precision.append(d)
    #         recall.append(e)
    #     print('Evaluation: AUC: %5.4f, F1: %5.4f, ACC: %5.4f, PRECISION: %5.4f, RECALL: %5.4f' % (np.mean(auc), np.mean(f1), np.mean(acc), np.mean(precision), np.mean(recall)))
    #     result = 'Evaluation: AUC: %5.4f, F1: %5.4f, ACC: %5.4f, PRECISION: %5.4f, RECALL: %5.4f' % (np.mean(auc), np.mean(f1), np.mean(acc), np.mean(precision), np.mean(recall))
    # print("Metric Complete")
    return result


def classify_image(M):
    img = M
    hist = cv2.calcHist([img],[0],None,[256],[0,256])
    
    concentration_h = np.sum(hist[200:256])
    concentration_l = np.sum(hist[0:50])
    concentration = max(concentration_h, concentration_l)

    distribution_range = np.sum(hist > 0) #  and distribution_range < 50

    threshold = 0.8
    
    # 分类和置信度逻辑
    if concentration > threshold * np.sum(hist):
        category = "Real"
        confidence = min(1.0, concentration / np.sum(hist))
    else:
        category = "Fake"
        confidence = (-1 / (2*threshold - 1)) * min(1.0, concentration / np.sum(hist)) + (4*threshold - 1) / (4*threshold - 2)
    
    return {"labels": category, "scores": confidence}


def decompose(test_path, test_size):
    # flist = sorted(os.listdir(test_path))
    
    size_list = [int(test_size)]
    for size in size_list:
        path_out = 'data/ImageFornsicsOSN/tmp/input_decompose_' + str(size) + '/'
        rm_and_make_dir(path_out)
    rtn_list = [[]]
    # for file in flist:
    file = test_path
    # img = cv2.imread(test_path + file)
    img = cv2.imread(test_path)
    # img = cv2.rotate(img, cv2.cv2.ROTATE_180)
    H, W, _ = img.shape
    size_idx = 0
    while size_idx < len(size_list) - 1:
        if H < size_list[size_idx+1] or W < size_list[size_idx+1]:
            break
        size_idx += 1
    rtn_list[size_idx].append(file)
    size = size_list[size_idx]
    path_out = 'data/ImageFornsicsOSN/tmp/input_decompose_' + str(size) + '/'
    X, Y = H // (size // 2) + 1, W // (size // 2) + 1
    idx = 0
    for x in range(X-1):
        if x * size // 2 + size > H:
            break
        for y in range(Y-1):
            if y * size // 2 + size > W:
                break
            img_tmp = img[x * size // 2: x * size // 2 + size, y * size // 2: y * size // 2 + size, :]
            cv2.imwrite(path_out + file[:-4] + '_%03d.png' % idx, img_tmp)
            idx += 1
        img_tmp = img[x * size // 2: x * size // 2 + size, -size:, :]
        cv2.imwrite(path_out + file[:-4] + '_%03d.png' % idx, img_tmp)
        idx += 1
    for y in range(Y - 1):
        if y * size // 2 + size > W:
            break
        img_tmp = img[-size:, y * size // 2: y * size // 2 + size, :]
        cv2.imwrite(path_out + file[:-4] + '_%03d.png' % idx, img_tmp)
        idx += 1
    img_tmp = img[-size:, -size:, :]
    cv2.imwrite(path_out + os.path.basename(file)[:-4] + '_%03d.png' % idx, img_tmp)
    idx += 1
    return rtn_list


def merge(path, test_size):
    path_d = 'data/ImageFornsicsOSN/tmp/input_decompose_' + test_size + '_pred/'
    path_r = 'data/ImageFornsicsOSN/output/'
    rm_and_make_dir(path_r)
    size = int(test_size)

    gk = gkern(size)
    gk = 1 - gk

    # for file in sorted(os.listdir(path)):
    # img = cv2.imread(path + file)
    file = path
    img = cv2.imread(path)
    H, W, _ = img.shape
    X, Y = H // (size // 2) + 1, W // (size // 2) + 1
    idx = 0
    rtn = np.ones((H, W, 3), dtype=np.float32) * -1
    for x in range(X-1):
        if x * size // 2 + size > H:
            break
        for y in range(Y-1):
            if y * size // 2 + size > W:
                break
            img_tmp = cv2.imread(path_d + file[:-4] + '_%03d.png' % idx)
            weight_cur = copy.deepcopy(rtn[x * size // 2: x * size // 2 + size, y * size // 2: y * size // 2 + size, :])
            h1, w1, _ = weight_cur.shape
            gk_tmp = cv2.resize(gk, (w1, h1))
            weight_cur[weight_cur != -1] = gk_tmp[weight_cur != -1]
            weight_cur[weight_cur == -1] = 0
            weight_tmp = copy.deepcopy(weight_cur)
            weight_tmp = 1 - weight_tmp
            rtn[x * size // 2: x * size // 2 + size, y * size // 2: y * size // 2 + size, :] = weight_cur * rtn[x * size // 2: x * size // 2 + size, y * size // 2: y * size // 2 + size, :] + weight_tmp * img_tmp
            idx += 1
        img_tmp = cv2.imread(path_d + file[:-4] + '_%03d.png' % idx)
        weight_cur = copy.deepcopy(rtn[x * size // 2: x * size // 2 + size, -size:, :])
        h1, w1, _ = weight_cur.shape
        gk_tmp = cv2.resize(gk, (w1, h1))
        weight_cur[weight_cur != -1] = gk_tmp[weight_cur != -1]
        weight_cur[weight_cur == -1] = 0
        weight_tmp = copy.deepcopy(weight_cur)
        weight_tmp = 1 - weight_tmp
        rtn[x * size // 2: x * size // 2 + size, -size:, :] = weight_cur * rtn[x * size // 2: x * size // 2 + size, -size:, :] + weight_tmp * img_tmp
        idx += 1
    for y in range(Y - 1):
        if y * size // 2 + size > W:
            break
        img_tmp = cv2.imread(path_d + file[:-4] + '_%03d.png' % idx)
        weight_cur = copy.deepcopy(rtn[-size:, y * size // 2: y * size // 2 + size, :])
        h1, w1, _ = weight_cur.shape
        gk_tmp = cv2.resize(gk, (w1, h1))
        weight_cur[weight_cur != -1] = gk_tmp[weight_cur != -1]
        weight_cur[weight_cur == -1] = 0
        weight_tmp = copy.deepcopy(weight_cur)
        weight_tmp = 1 - weight_tmp
        rtn[-size:, y * size // 2: y * size // 2 + size, :] = weight_cur * rtn[-size:, y * size // 2: y * size // 2 + size, :] + weight_tmp * img_tmp
        idx += 1
    img_tmp = cv2.imread(path_d + file[:-4] + '_%03d.png' % idx)
    weight_cur = copy.deepcopy(rtn[-size:, -size:, :])
    h1, w1, _ = weight_cur.shape
    gk_tmp = cv2.resize(gk, (w1, h1))
    weight_cur[weight_cur != -1] = gk_tmp[weight_cur != -1]
    weight_cur[weight_cur == -1] = 0
    weight_tmp = copy.deepcopy(weight_cur)
    weight_tmp = 1 - weight_tmp
    rtn[-size:, -size:, :] = weight_cur * rtn[-size:, -size:, :] + weight_tmp * img_tmp
    idx += 1
    # rtn[rtn < 127] = 0
    # rtn[rtn >= 127] = 255
    cv2.imwrite(path_r + file[:-4] + '.png', np.uint8(rtn))
    return path_r


def gkern(kernlen=7, nsig=3):
    """Returns a 2D Gaussian kernel."""
    # x = np.linspace(-nsig, nsig, kernlen+1)
    # kern1d = np.diff(st.norm.cdf(x))
    # kern2d = np.outer(kern1d, kern1d)
    # rtn = kern2d/kern2d.sum()
    # rtn = np.concatenate([rtn[..., None], rtn[..., None], rtn[..., None]], axis=2)
    rtn = [[0, 0, 0],
           [0, 1, 0],
           [0, 0, 0]]
    rtn = np.array(rtn, dtype=np.float32)
    rtn = np.concatenate([rtn[..., None], rtn[..., None], rtn[..., None]], axis=2)
    rtn = cv2.resize(rtn, (kernlen, kernlen))
    return rtn


def rm_and_make_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def metric(premask, groundtruth):
    seg_inv, gt_inv = np.logical_not(premask), np.logical_not(groundtruth)
    true_pos = float(np.logical_and(premask, groundtruth).sum())  # float for division
    true_neg = np.logical_and(seg_inv, gt_inv).sum()
    false_pos = np.logical_and(premask, gt_inv).sum()
    false_neg = np.logical_and(seg_inv, groundtruth).sum()
    acc = (true_pos + true_neg)/(true_pos + true_neg + false_pos + false_neg)
    precision = true_pos / (true_pos + false_pos)
    recall = true_pos / (true_pos + false_neg)
    f1 = 2 * true_pos / (2 * true_pos + false_pos + false_neg + 1e-6)
    cross = np.logical_and(premask, groundtruth)
    union = np.logical_or(premask, groundtruth)
    iou = np.sum(cross) / (np.sum(union) + 1e-6)
    if np.sum(cross) + np.sum(union) == 0:
        iou = 1
    return f1, iou, acc, precision, recall


def image_classification_main_function(model, url):
    """ 对接API的函数 """
    result = forensics_test(model=model, url=url)

    return result


if __name__ == '__main__':
    model = Model().cuda()
    model.load()
    model.eval()
    forensics_test(model=model, url='ImageFornsicsOSN/data/Columbia/canong3_canonxt_sub_01.tif')
