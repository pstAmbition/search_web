"""
Evaluates a folder of video files or a single file with a xception binary
classification network.

Usage:
python detect_from_video.py
    -i <folder with video files or path to video file>
    -m <path to model file>
    -o <path to output folder, will write one or multiple output videos there>

Author: Andreas Rössler
"""
import os
import argparse
import sys
sys.path.append("/home/lihr/Key_Research/flfx-003/FaceForensics/classification")
from os.path import join
import cv2
import dlib
import torch
import torch.nn as nn
from PIL import Image as pil_image
from tqdm import tqdm
import numpy as np
from sklearn.metrics import accuracy_score,f1_score,roc_auc_score,precision_score,recall_score
from network.models import model_selection
from dataset.transform import xception_default_data_transforms
# os.environ['CUDA_VISIBLE_DEVICES'] = '6'

def get_boundingbox(face, width, height, scale=1.3, minsize=None):
    """
    Expects a dlib face to generate a quadratic bounding box.
    :param face: dlib face class
    :param width: frame width
    :param height: frame height
    :param scale: bounding box size multiplier to get a bigger face region
    :param minsize: set minimum bounding box size
    :return: x, y, bounding_box_size in opencv form
    """
    x1 = face.left()
    y1 = face.top()
    x2 = face.right()
    y2 = face.bottom()
    size_bb = int(max(x2 - x1, y2 - y1) * scale)
    if minsize:
        if size_bb < minsize:
            size_bb = minsize
    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

    # Check for out of bounds, x-y top left corner
    x1 = max(int(center_x - size_bb // 2), 0)
    y1 = max(int(center_y - size_bb // 2), 0)
    # Check for too big bb size for given x, y
    size_bb = min(width - x1, size_bb)
    size_bb = min(height - y1, size_bb)

    return x1, y1, size_bb


def preprocess_image(image, cuda=True):
    """
    Preprocesses the image such that it can be fed into our network.
    During this process we envoke PIL to cast it into a PIL image.

    :param image: numpy image in opencv form (i.e., BGR and of shape
    :return: pytorch tensor of shape [1, 3, image_size, image_size], not
    necessarily casted to cuda
    """
    # Revert from BGR
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Preprocess using the preprocessing function used during training and
    # casting it to PIL image
    preprocess = xception_default_data_transforms['test']
    preprocessed_image = preprocess(pil_image.fromarray(image))
    # Add first dimension as the network expects a batch
    preprocessed_image = preprocessed_image.unsqueeze(0)
    if cuda:
        preprocessed_image = preprocessed_image.cuda()
    return preprocessed_image


def predict_with_model(image, model, post_function=nn.Softmax(dim=1),
                       cuda=True):
    """
    Predicts the label of an input image. Preprocesses the input image and
    casts it to cuda if required

    :param image: numpy image
    :param model: torch model with linear layer at the end
    :param post_function: e.g., softmax
    :param cuda: enables cuda, must be the same parameter as the model
    :return: prediction (1 = fake, 0 = real)
    """
    # Preprocess
    preprocessed_image = preprocess_image(image, cuda)

    # Model prediction
    output = model(preprocessed_image)
    output = post_function(output)

    # Cast to desired
    _, prediction = torch.max(output, 1)    # argmax
    prediction = float(prediction.cpu().numpy())

    return int(prediction), output


def test_full_image_network(video_fake_path, video_real_path, model, output_path,
                            start_frame=0, end_frame=None, cuda=True, is_fake=True):
    """
    Reads a video and evaluates a subset of frames with the a detection network
    that takes in a full frame. Outputs are only given if a face is present
    and the face is highlighted using dlib.
    :param video_path: path to video file
    :param model_path: path to model file (should expect the full sized image)
    :param output_path: path where the output video is stored
    :param start_frame: first frame to evaluate
    :param end_frame: last frame to evaluate
    :param cuda: enable cuda
    :return:
    """
    if is_fake:
        # print('Starting: {}'.format(video_fake_path))
        # Read and write
        reader = cv2.VideoCapture(video_fake_path)
        video_fn = video_fake_path.split('/')[-1].split('.')[0]+'.avi'
    else:
        # print('Starting: {}'.format(video_real_path))
        # Read and write
        reader = cv2.VideoCapture(video_real_path)
        video_fn = video_real_path.split('/')[-1].split('.')[0]+'.avi'


    os.makedirs(output_path, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    fps = reader.get(cv2.CAP_PROP_FPS)
    num_frames = int(reader.get(cv2.CAP_PROP_FRAME_COUNT))
    writer = None

    # Face detector
    face_detector = dlib.get_frontal_face_detector()

    # Text variables
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    font_scale = 1

    # Frame numbers and length of output video
    frame_num = 0
    assert start_frame < num_frames - 1
    end_frame = end_frame if end_frame else num_frames
    # pbar = tqdm(total=end_frame-start_frame)

    pre_list = []
    true_list = []
    probabilities_list = []
    gap = 100

    while reader.isOpened():
        for i in range(gap):
            _, image = reader.read()
        if image is None:
            break
        frame_num += gap

        if frame_num < start_frame:
            continue
        # pbar.update(gap)

        # Image size
        height, width = image.shape[:2]

        # Init output writer
        if writer is None:
            writer = cv2.VideoWriter(join(output_path, video_fn), fourcc, fps,
                                     (height, width)[::-1])

        # 2. Detect with dlib
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray, 1)
        if len(faces):
            # For now only take biggest face
            face = faces[0]

            # --- Prediction ---------------------------------------------------
            # Face crop with dlib and bounding box scale enlargement
            x, y, size = get_boundingbox(face, width, height)
            cropped_face = image[y:y+size, x:x+size]

            # Actual prediction using our model
            prediction, output = predict_with_model(cropped_face, model,
                                                    cuda=cuda)
            # ------------------------------------------------------------------
            probabilities = output[0][1].detach().cpu().numpy()
            pre_list.append(prediction)
            
            probabilities_list.append(probabilities)
            if(is_fake):
                true_list.append(1)
            else:
                true_list.append(0)
            # Text and bb
            x = face.left()
            y = face.top()
            w = face.right() - x
            h = face.bottom() - y
            label = 'fake' if prediction == 1 else 'real'
            color = (0, 255, 0) if prediction == 0 else (0, 0, 255)
            output_list = ['{0:.2f}'.format(float(x)) for x in
                           output.detach().cpu().numpy()[0]]
            cv2.putText(image, str(output_list)+'=>'+label, (x, y+h+30),
                        font_face, font_scale,
                        color, thickness, 2)
            # draw box over face
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

        if frame_num >= end_frame:
            break

        # Show
        # cv2.imshow('test', image)
        # cv2.waitKey(33)     # About 30 fps
        writer.write(image)
    # pbar.close()
    # if writer is not None:
    #     writer.release()
    #     print('Finished! Output saved under {}'.format(output_path))
    # else:
    #     print('Input video file was empty')

    return pre_list, true_list, probabilities_list


def video_classification_main_function(model, url):
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--video_fake_path', '-i', default="altered", type=str)
    p.add_argument('--video_real_path', default="original", type=str)
    p.add_argument('--model', '-m', type=str, default="")
    p.add_argument('--output_path', '-o', type=str,
                   default='data/output')
    p.add_argument('--start_frame', type=int, default=0)
    p.add_argument('--end_frame', type=int, default=None)
    p.add_argument('--cuda', default=True)
    p.add_argument('--is_fake', default=True)
    args = p.parse_args()

    # args.video_fake_path = os.path.join(url, args.video_fake_path)
    # args.video_real_path = os.path.join(url, args.video_real_path)
    args.model = model

    pre_list = []
    true_list = []
    probabilities_list = []
    video_fake_path = args.video_fake_path
    video_real_path = args.video_real_path
    if video_fake_path.endswith('.mp4') or video_fake_path.endswith('.avi'):
        pre_list, true_list = test_full_image_network(**vars(args))
    else:
        fake_videos = os.listdir(video_fake_path)
        videos_fake_10 = fake_videos[:10] #抽样
        for video in tqdm(fake_videos):
            args.video_fake_path = join(video_fake_path, video)
            tqdm.write('Starting: {}'.format(args.video_fake_path))
            pre, tr, pro = test_full_image_network(**vars(args))
            pre_list = pre_list + pre
            true_list = true_list + tr
            probabilities_list = probabilities_list + pro

        real_videos = os.listdir(video_real_path)
        videos_real_10 = real_videos[:10] #抽样
        for video in tqdm(real_videos):
            args.video_real_path = join(video_real_path, video)
            tqdm.write('Starting: {}'.format(args.video_real_path))
            args.is_fake = False
            pre, tr, pro = test_full_image_network(**vars(args))
            pre_list = pre_list + pre
            true_list = true_list + tr
            probabilities_list = probabilities_list + pro

    acc = accuracy_score(true_list, pre_list)
    f1 = f1_score(true_list, pre_list)
    recall = recall_score(true_list,pre_list)
    precision = precision_score(true_list,pre_list)
    auc = roc_auc_score(true_list, probabilities_list)
    print('Evaluation: AUC: %5.4f, F1: %5.4f, ACC: %5.4f, Recall: %5.4f, Precision: %5.4f' % (auc, f1, acc, recall, precision))
    result = 'Evaluation: AUC: %5.4f, F1: %5.4f, ACC: %5.4f, Recall: %5.4f, Precision: %5.4f' % (auc, f1, acc, recall, precision)
    return result

if __name__ == '__main__':
    url = "./classification/test/"
    model_path = "./classification/models/models_subset/full/xception/full_raw.p"
    model = torch.load(model_path)
    video_classification_main_function(model=model, url=url)

