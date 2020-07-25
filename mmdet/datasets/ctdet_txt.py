from .txt_style import txtDataset
from .registry import DATASETS
import numpy as np
import cv2
import os
import math
import time
# import torch

def get_dir(src_point, rot_rad):
    sn, cs = np.sin(rot_rad), np.cos(rot_rad)

    src_result = [0, 0]
    src_result[0] = src_point[0] * cs - src_point[1] * sn
    src_result[1] = src_point[0] * sn + src_point[1] * cs

    return src_result

def get_3rd_point(a, b):
    direct = a - b
    return b + np.array([-direct[1], direct[0]], dtype=np.float32)

def get_affine_transform(center,
                         scale,
                         rot,
                         output_size,
                         shift=np.array([0, 0], dtype=np.float32),
                         inv=0):
    if not isinstance(scale, np.ndarray) and not isinstance(scale, list):
        scale = np.array([scale, scale], dtype=np.float32)

    scale_tmp = scale
    src_w = scale_tmp[0]
    dst_w = output_size[0]
    dst_h = output_size[1]

    rot_rad = np.pi * rot / 180
    src_dir = get_dir([0, src_w * -0.5], rot_rad)
    dst_dir = np.array([0, dst_w * -0.5], np.float32)

    src = np.zeros((3, 2), dtype=np.float32)
    dst = np.zeros((3, 2), dtype=np.float32)
    src[0, :] = center + scale_tmp * shift
    src[1, :] = center + src_dir + scale_tmp * shift
    dst[0, :] = [dst_w * 0.5, dst_h * 0.5]
    dst[1, :] = np.array([dst_w * 0.5, dst_h * 0.5], np.float32) + dst_dir

    src[2:, :] = get_3rd_point(src[0, :], src[1, :])
    dst[2:, :] = get_3rd_point(dst[0, :], dst[1, :])

    if inv:
        trans = cv2.getAffineTransform(np.float32(dst), np.float32(src))
    else:
        trans = cv2.getAffineTransform(np.float32(src), np.float32(dst))

    return trans

def gaussian_radius(det_size, min_overlap=0.7):
    height, width = det_size

    a1  = 1
    b1  = (height + width)
    c1  = width * height * (1 - min_overlap) / (1 + min_overlap)
    sq1 = np.sqrt(b1 ** 2 - 4 * a1 * c1)
    r1  = (b1 + sq1) / 2

    a2  = 4
    b2  = 2 * (height + width)
    c2  = (1 - min_overlap) * width * height
    sq2 = np.sqrt(b2 ** 2 - 4 * a2 * c2)
    r2  = (b2 + sq2) / 2

    a3  = 4 * min_overlap
    b3  = -2 * min_overlap * (height + width)
    c3  = (min_overlap - 1) * width * height
    sq3 = np.sqrt(b3 ** 2 - 4 * a3 * c3)
    r3  = (b3 + sq3) / 2
    return min(r1, r2, r3)

def gaussian2D(shape, sigma=1):
    m, n = [(ss - 1.) / 2. for ss in shape]
    y, x = np.ogrid[-m:m+1,-n:n+1]

    h = np.exp(-(x * x + y * y) / (2 * sigma * sigma))
    h[h < np.finfo(h.dtype).eps * h.max()] = 0
    return h

def draw_umich_gaussian(heatmap, center, radius, k=1):
    diameter = 2 * radius + 1
    gaussian = gaussian2D((diameter, diameter), sigma=diameter / 6)

    x, y = int(center[0]), int(center[1])

    height, width = heatmap.shape[0:2]

    left, right = min(x, radius), min(width - x, radius + 1)
    top, bottom = min(y, radius), min(height - y, radius + 1)

    masked_heatmap  = heatmap[y - top:y + bottom, x - left:x + right]
    masked_gaussian = gaussian[radius - top:radius + bottom, radius - left:radius + right]
    if min(masked_gaussian.shape) > 0 and min(masked_heatmap.shape) > 0: # TODO debug
        np.maximum(masked_heatmap, masked_gaussian * k, out=masked_heatmap)
    return heatmap

def affine_transform(pt, t):
    new_pt = np.array([pt[0], pt[1], 1.], dtype=np.float32).T
    new_pt = np.dot(t, new_pt)
    return new_pt[:2]

@DATASETS.register_module
class Ctdet_txt(txtDataset):

#     # for Visdrone
#     CLASSES = ['__background__', "aeroplane", "bicycle", "bird", "boat",
#      "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog",
#      "horse", "motorbike", "person", "pottedplant", "sheep", "sofa",
#      "train", "tvmonitor"]

#     # for coco
#     CLASSES = ('person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
#                'train', 'truck', 'boat', 'traffic_light', 'fire_hydrant',
#                'stop_sign', 'parking_meter', 'bench', 'bird', 'cat', 'dog',
#                'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
#                'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
#                'skis', 'snowboard', 'sports_ball', 'kite', 'baseball_bat',
#                'baseball_glove', 'skateboard', 'surfboard', 'tennis_racket',
#                'bottle', 'wine_glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
#                'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
#                'hot_dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
#                'potted_plant', 'bed', 'dining_table', 'toilet', 'tv', 'laptop',
#                'mouse', 'remote', 'keyboard', 'cell_phone', 'microwave',
#                'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
#                'vase', 'scissors', 'teddy_bear', 'hair_drier', 'toothbrush')

    def __init__(self, **kwargs):
        super(Ctdet_txt, self).__init__(**kwargs)
#         self.use_coco = use_coco
#         print(kwargs)

    def _get_border(self, border, size): # 128, width (800-1000?)
        i = 1
        while size - border // i <= border // i:
            i *= 2
        return border // i

    def _coco_box_to_bbox(self, box):
        bbox = np.array([box[0], box[1], box[0] + box[2], box[1] + box[3]],
                        dtype=np.float32)
        return bbox

    def prepare_train_img(self, index):
        self.max_objs = 128
        self.num_classes = 10
#         if self.use_coco:
#             self.max_objs = 128
#             self.num_classes = 80
#             _valid_ids = [
#               1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13,
#               14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
#               24, 25, 27, 28, 31, 32, 33, 34, 35, 36,
#               37, 38, 39, 40, 41, 42, 43, 44, 46, 47,
#               48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
#               58, 59, 60, 61, 62, 63, 64, 65, 67, 70,
#               72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
#               82, 84, 85, 86, 87, 88, 89, 90]
#             cat_ids = {v: i for i, v in enumerate(_valid_ids)}
#         else:
#             self.max_objs = 50
#             self.num_classes = 21
#             cat_ids = {v: i for i, v in enumerate(np.arange(1, 21, dtype=np.int32))}

        # import pdb; pdb.set_trace()
        img_info = self.img_infos[index]
        img_id = img_info['id']
        file_name = img_info['filename']
        img_path =  os.path.join(self.img_prefix, file_name)
        
#         id=img_id, filename=filename, width=width, height=height)
#         file_name = self.coco.loadImgs(ids=[img_id])[0]['file_name']
#         img_path =os.path.join(self.img_prefix, file_name)
#         ann_ids = self.coco.getAnnIds(imgIds=[img_id])
#         anns = self.coco.loadAnns(ann_ids)
        anns = self.get_ann_info(index)
#         dict(
#             bboxes=bboxes.astype(np.float32),
#             labels=labels.astype(np.int64),
#             bboxes_ignore=bboxes_ignore.astype(np.float32),
#             labels_ignore=labels_ignore.astype(np.int64))
#         bboxes = anns["bboxes"].tolist() # (xmin, ymin, xmax, ymax) numpy (, 4)
#         labels = anns["labels"].tolist()
        bboxes = anns["bboxes"]
        labels = anns["labels"]
        
        num_objs = min(bboxes.shape[0], self.max_objs)

        img = cv2.imread(img_path) # h, w, c
        height, width = img.shape[0], img.shape[1]
        c = np.array([img.shape[1] / 2., img.shape[0] / 2.], dtype=np.float32)
        # if self.opt.keep_res:
#         input_h = (height | self.size_divisor) + 1
#         input_w = (width | self.size_divisor) + 1
#         input_h = height
#         input_w = width
#         s = np.array([input_w, input_h], dtype=np.float32)
        # else:
        s = max(img.shape[0], img.shape[1]) * 1.0
        input_h, input_w = self.img_scales[0][1], self.img_scales[0][0]

        # flipped = False
        # if self.split == 'train':
        #   if not self.opt.not_rand_crop:
        s = s * np.random.choice(np.arange(0.6, 1.4, 0.1))
        w_border = self._get_border(256, img.shape[1])
        h_border = self._get_border(256, img.shape[0])
        c[0] = np.random.randint(low=w_border, high=img.shape[1] - w_border)
        c[1] = np.random.randint(low=h_border, high=img.shape[0] - h_border)
        #   else:
        # sf = 0.4
        # cf = 0.1
        # c[0] += s * np.clip(np.random.randn()*cf, -2*cf, 2*cf)
        # c[1] += s * np.clip(np.random.randn()*cf, -2*cf, 2*cf)
        # s = s * np.clip(np.random.randn()*sf + 1, 1 - sf, 1 + sf)

        #   if np.random.random() < self.opt.flip:
        #     flipped = True
        #     img = img[:, ::-1, :]
        #     c[0] =  width - c[0] - 1

        trans_input = get_affine_transform(
          c, s, 0, [input_w, input_h])
#         meta = {}
#         meta['c'] = c
#         meta['s'] = s
     
        inp = cv2.warpAffine(img, trans_input,
                             (input_w, input_h),
                             flags=cv2.INTER_LINEAR)
        inp = (inp.astype(np.float32) / 255.)
        inp = (inp - self.img_norm_cfg['mean']) / self.img_norm_cfg['std']
        inp = inp.transpose(2, 0, 1)

        output_h = input_h // 4
        output_w = input_w // 4
#         print(output_h, output_w)
#         meta['out_height'] = output_h
#         meta['out_width'] = output_w
        trans_output = get_affine_transform(c, s, 0, [output_w, output_h])

        hm = np.zeros((self.num_classes, output_h, output_w), dtype=np.float32)
        wh = np.zeros((self.max_objs, 2), dtype=np.float32)
        reg = np.zeros((self.max_objs, 2), dtype=np.float32)
        ind = np.zeros((self.max_objs), dtype=np.int64)
        reg_mask = np.zeros((self.max_objs), dtype=np.uint8)

        for k in range(num_objs):
#             ann = anns[k]
#             bbox = self._coco_box_to_bbox(ann['bbox']) # 输入网络 x1, y1, x2, y2
#             cls_id = int(cat_ids[ann['category_id']])
            bbox = bboxes[k] # (4), numpy
            cls_id = int(labels[k]) - 1
            # tranform bounding box to output size
            bbox[:2] = affine_transform(bbox[:2], trans_output)
            bbox[2:] = affine_transform(bbox[2:], trans_output)
            bbox[[0, 2]] = np.clip(bbox[[0, 2]], 0, output_w - 1)
            bbox[[1, 3]] = np.clip(bbox[[1, 3]], 0, output_h - 1)
            h, w = bbox[3] - bbox[1], bbox[2] - bbox[0]
            print("h, w", h, w)
            if h > 0 and w > 0:
                # populate hm based on gd and ct
                radius = gaussian_radius((math.ceil(h), math.ceil(w)))
                radius = max(0, int(radius))
                ct = np.array(
                  [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2], dtype=np.float32)
                print(ct)
                ct_int = ct.astype(np.int32)
                print(ct_int)
                draw_umich_gaussian(hm[cls_id], ct_int, radius)
                wh[k] = 1. * w, 1. * h
                ind[k] = ct_int[1] * output_w + ct_int[0]
                reg[k] = ct - ct_int
                reg_mask[k] = 1

        ret = {'img': inp, 'hm': hm, 'reg_mask': reg_mask, 'ind': ind, 'wh': wh, 'reg': reg, 'img_meta':[]}
        return ret
    
    def prepare_test_img(self, index):
        
        self.max_objs = 128
        self.num_classes = 10
        
        img_info = self.img_infos[index]
        img_id = img_info['id']
        file_name = img_info['filename']
        img_path =  os.path.join(self.img_prefix, file_name)

        img = cv2.imread(img_path)
        height, width = img.shape[0], img.shape[1]
        c = np.array([img.shape[1] / 2., img.shape[0] / 2.], dtype=np.float32)
        
        s = max(img.shape[0], img.shape[1]) * 1.0
        input_h, input_w = self.img_scales[0][1], self.img_scales[0][0]
        
        
        trans_input = get_affine_transform(c, s, 0, [input_w, input_h])
        
        inp = cv2.warpAffine(img, trans_input,
                             (input_w, input_h),
                             flags=cv2.INTER_LINEAR)
        
        inp = (inp.astype(np.float32) / 255.)
        inp = (inp - self.img_norm_cfg['mean']) / self.img_norm_cfg['std']
        inp = inp.transpose(2, 0, 1) # reshape(1, 3, inp_height, inp_width)

        output_h = input_h // 4
        output_w = input_w // 4
        
        meta = {'c': c, 's': s, 
                'out_height': output_h, 
                'out_width': output_w}
        
        ret = {"img": inp, "img_meta": meta}
        return ret
