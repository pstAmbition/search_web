import copy
import torch
import numpy as np
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, confusion_matrix
from tqdm import tqdm
from dataset import FeatureDataset
from model import SimilarityModule, DetectionModule
import torch.nn.functional as F
import random

# Configs
DEVICE = "cuda:0"
NUM_WORKER = 1
BATCH_SIZE = 64
LR = 1e-3
L2 = 0  # 1e-5
NUM_EPOCH = 100
def set_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def prepare_data(text, image, label):
    nr_index = [i for i, l in enumerate(label) if l == 1]
    text_nr = text[nr_index]
    image_nr = image[nr_index]
    fixed_text = copy.deepcopy(text_nr)
    matched_image = copy.deepcopy(image_nr)
    unmatched_image = copy.deepcopy(image_nr).roll(shifts=3, dims=0)
    return fixed_text, matched_image, unmatched_image

def multimodal_classification_for_one_sample(text_feature_path, image_feature_path, data_index):
    # ---  Load Config  ---
    device = torch.device(DEVICE)
    set_seed()
    
    # ---  Load Data  ---
    test_set = FeatureDataset(
        text_feature_path,
        image_feature_path
    )
    # ---  Build Model & Trainer  ---
    similarity_module = torch.load('similarity_module.pt') # SimilarityModule()  
    similarity_module.to(device)
    detection_module = torch.load('detection_module.pt') # DetectionModule()  
    detection_module.to(device)

    # ---  Test  ---

    similarity_module.eval()
    detection_module.eval()

    device = torch.device(DEVICE)

    with torch.no_grad():
        text, image, label = test_set[data_index]

        # text = text.unsqueeze(0).to(device)
        # image = image.unsqueeze(0).to(device)
        # label = label.unsqueeze(0).to(device)
        text = text.unsqueeze(0).repeat(BATCH_SIZE, 1, 1).to(device)
        image = image.unsqueeze(0).repeat(BATCH_SIZE, 1).to(device)
        label = label.repeat(BATCH_SIZE).to(device)
        # print(type(text))
        # print(text.shape)
        # print(type(image))
        # print(image.shape)
        # print(type(label))
        # print(label.shape)
        # exit()
        
        # fixed_text, matched_image, unmatched_image = prepare_data(text, image, label)
        # fixed_text.to(device)
        # matched_image.to(device)
        # unmatched_image.to(device)


        # ---  TASK2 Detection  ---

        text_aligned, image_aligned, _ = similarity_module(text, image)
        # print(text_aligned[0,:3])
        pre_detection = detection_module(text, image, text_aligned, image_aligned)
        # print(pre_detection[:3])
        pre_label_detection = pre_detection.argmax(1)
        # 对第二维进行softmax操作
        softmaxed = F.softmax(pre_detection, dim=1)

        # 获取每行的最大值
        probs, _ = torch.max(softmaxed, dim=1)
    
    # print('predict label:', pre_label_detection[0].cpu().item(), 'groundtruth:',label[0].cpu().item(), 'predict probs:', probs[0].cpu().item())

    return pre_label_detection[0].cpu().item(),label[0].cpu().item(), probs[0].cpu().item()
    

def multimodal_classification():
    # ---  Load Config  ---
    device = torch.device(DEVICE)
    num_workers = NUM_WORKER
    batch_size = BATCH_SIZE
    lr = LR
    l2 = L2
    num_epoch = NUM_EPOCH
    
    # ---  Load Data  ---
    dataset_dir = 'data/twitter'
    test_set = FeatureDataset(
        "{}/test_text_with_label.npz".format(dataset_dir),
        "{}/test_image_with_label.npz".format(dataset_dir)
    )
    test_loader = DataLoader(
        test_set, batch_size=batch_size, num_workers=num_workers, shuffle=False
    )

    # ---  Build Model & Trainer  ---
    similarity_module = torch.load('similarity_module.pt') # SimilarityModule()  
    similarity_module.to(device)
    detection_module = torch.load('detection_module.pt') # DetectionModule()  
    detection_module.to(device)

    # ---  Test  ---

    acc_similarity_test, acc_detection_test, loss_similarity_test, loss_detection_test, cm_similarity, cm_detection = test(similarity_module, detection_module, test_loader)

    print('---  TASK Detection  ---')
    print(
        "acc_detection_test = %.3f \n loss_detection_test = %.3f \n" %
        (acc_detection_test, loss_detection_test)
    )
    return "acc_detection_test = %.3f  loss_detection_test = %.3f " % (acc_detection_test, loss_detection_test)


def test(similarity_module, detection_module, test_loader):
    similarity_module.eval()
    detection_module.eval()

    device = torch.device(DEVICE)
    loss_func_detection = torch.nn.CrossEntropyLoss()
    loss_func_similarity = torch.nn.CosineEmbeddingLoss()

    similarity_count = 0
    detection_count = 0
    loss_similarity_total = 0
    loss_detection_total = 0
    similarity_label_all = []
    detection_label_all = []
    similarity_pre_label_all = []
    detection_pre_label_all = []

    with torch.no_grad():
        for i, (text, image, label) in enumerate(test_loader):
            # print(type(text))
            # print(text.shape)
            # print(type(image))
            # print(image.shape)
            # print(type(label))
            # print(label.shape)
            # exit()
            batch_size = text.shape[0]
            text = text.to(device)
            image = image.to(device)
            label = label.to(device)
            
            fixed_text, matched_image, unmatched_image = prepare_data(text, image, label)
            fixed_text.to(device)
            matched_image.to(device)
            unmatched_image.to(device)

            # ---  TASK1 Similarity  ---

            text_aligned_match, image_aligned_match, pred_similarity_match = similarity_module(fixed_text, matched_image)
            text_aligned_unmatch, image_aligned_unmatch, pred_similarity_unmatch = similarity_module(fixed_text, unmatched_image)
            similarity_pred = torch.cat([pred_similarity_match.argmax(1), pred_similarity_unmatch.argmax(1)], dim=0)
            similarity_label_0 = torch.cat([torch.ones(pred_similarity_match.shape[0]), torch.zeros(pred_similarity_unmatch.shape[0])], dim=0).to(device)
            similarity_label_1 = torch.cat([torch.ones(pred_similarity_match.shape[0]), -1 * torch.ones(pred_similarity_unmatch.shape[0])], dim=0).to(device)

            text_aligned_4_task1 = torch.cat([text_aligned_match, text_aligned_unmatch], dim=0)
            image_aligned_4_task1 = torch.cat([image_aligned_match, image_aligned_unmatch], dim=0)
            loss_similarity = loss_func_similarity(text_aligned_4_task1, image_aligned_4_task1, similarity_label_1)

            # ---  TASK2 Detection  ---

            text_aligned, image_aligned, _ = similarity_module(text, image)
            pre_detection = detection_module(text, image, text_aligned, image_aligned)
            loss_detection = loss_func_detection(pre_detection, label)
            pre_label_detection = pre_detection.argmax(1)

            # ---  Record  ---

            loss_similarity_total += loss_similarity.item() * (2 * fixed_text.shape[0])
            loss_detection_total += loss_detection.item() * text.shape[0]
            similarity_count += (fixed_text.shape[0] * 2)
            detection_count += text.shape[0]

            similarity_pre_label_all.append(similarity_pred.detach().cpu().numpy())
            detection_pre_label_all.append(pre_label_detection.detach().cpu().numpy())
            similarity_label_all.append(similarity_label_0.detach().cpu().numpy())
            detection_label_all.append(label.detach().cpu().numpy())

        loss_similarity_test = loss_similarity_total / similarity_count
        loss_detection_test = loss_detection_total / detection_count

        similarity_pre_label_all = np.concatenate(similarity_pre_label_all, 0)
        detection_pre_label_all = np.concatenate(detection_pre_label_all, 0)
        similarity_label_all = np.concatenate(similarity_label_all, 0)
        detection_label_all = np.concatenate(detection_label_all, 0)

        acc_similarity_test = accuracy_score(similarity_pre_label_all, similarity_label_all)
        acc_detection_test = accuracy_score(detection_pre_label_all, detection_label_all)
        cm_similarity = confusion_matrix(similarity_pre_label_all, similarity_label_all)
        cm_detection = confusion_matrix(detection_pre_label_all, detection_label_all)

    return acc_similarity_test, acc_detection_test, loss_similarity_test, loss_detection_test, cm_similarity, cm_detection



def text_encoder(text="BREAKING: Nancy Pelosi Was Just Taken From Her Office In Handcuffs"):
    from transformers import BertTokenizer, BertModel

    tokenizer = BertTokenizer.from_pretrained('./models/bert-base-uncased')
    bert = BertModel.from_pretrained('./models/bert-base-uncased')
    inputs = tokenizer(text, return_tensors="pt", padding='max_length', truncation=True, max_length=30)  # "pt"表示"pytorch"
    outputs = bert(**inputs)
    hs = outputs.last_hidden_state[0]
    hs = hs[:,:200] #.permute(1, 0)
    # print(hs.shape)
    return hs

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
from PIL import Image


class ResNet34FeatureExtractor(nn.Module):
    def __init__(self):
        super(ResNet34FeatureExtractor, self).__init__()
        # Load the pretrained ResNet-34 model
        self.resnet34 = models.resnet34(pretrained=True)
        # Remove the last fully connected layer
        self.resnet34 = nn.Sequential(*list(self.resnet34.children())[:-1])
        # # Add a new fully connected layer with 512 output features
        # self.fc = nn.Linear(self.resnet34[-1].in_features, 512)

    def forward(self, x):
        # Pass the input through the ResNet-34 model
        x = self.resnet34(x)
        # Flatten the output
        x = x.view(x.size(0), -1)
        # Pass the output through the new fully connected layer
        # x = self.fc(x)
        return x

# Function to preprocess the input image
def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)  # Add batch dimension
    return image

# Function to extract features from an image
def image_encoder(image_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ResNet34FeatureExtractor().to(device)
    model.eval()  # Set model to evaluation mode

    image = preprocess_image(image_path).to(device)
    with torch.no_grad():
        features = model(image)
    return features[0]


def multimodal_classification_for_one_sample_with_raw_input(text, image):
    # ---  Load Config  ---
    device = torch.device(DEVICE)
    set_seed()
    
    # ---  Build Model & Trainer  ---
    similarity_module = torch.load('similarity_module.pt') # SimilarityModule()  
    similarity_module.to(device)
    detection_module = torch.load('detection_module.pt') # DetectionModule()  
    detection_module.to(device)

    # ---  Test  ---

    similarity_module.eval()
    detection_module.eval()

    device = torch.device(DEVICE)

    with torch.no_grad():
        text = text_encoder(text)
        image = image_encoder(image)

        text = text.unsqueeze(0).repeat(BATCH_SIZE, 1, 1).to(device)
        image = image.unsqueeze(0).repeat(BATCH_SIZE, 1).to(device)

        # ---  TASK2 Detection  ---

        text_aligned, image_aligned, _ = similarity_module(text, image)
        # print(text_aligned[0,:3])
        pre_detection = detection_module(text, image, text_aligned, image_aligned)
        # print(pre_detection[:3])
        pre_label_detection = pre_detection.argmax(1)
        # 对第二维进行softmax操作
        softmaxed = F.softmax(pre_detection, dim=1)

        # 获取每行的最大值
        probs, _ = torch.max(softmaxed, dim=1)
    
    # print('predict label:', pre_label_detection[0].cpu().item(), 'groundtruth:',label[0].cpu().item(), 'predict probs:', probs[0].cpu().item())

    return pre_label_detection[0].cpu().item(), probs[0].cpu().item()

if __name__ == "__main__":
    # multimodal_classification()
    # multimodal_classification_for_one_sample('data/twitter/test_text_with_label.npz', 'data/twitter/test_image_with_label.npz', 0)
    print(multimodal_classification_for_one_sample_with_raw_input("BREAKING: Nancy Pelosi Was Just Taken From Her Office In Handcuffs", "./fake_news.png"))

