# model settings
model = dict(
    type='CenterNetFPN',
    #pretrained='open-mmlab://resnet50_caffe',
    #backbone=dict(
    #    type='ResNet',
    #    depth=50,
    #    num_stages=4,
    #    out_indices=(0, 1, 2, 3),
    #    frozen_stages=1,
    #    norm_cfg=dict(type='BN', requires_grad=False),
    #    style='caffe'),
    #neck=dict(
    #    type='FPN',
    #    in_channels=[256, 512, 1024, 2048],
    #    out_channels=256,
    #    start_level=1,
    #    add_extra_convs=True,
    #    extra_convs_on_inputs=False,  # use P5
    #    num_outs=5,
    #    relu_before_extra_convs=True),
    backbone=dict(
        type='HRNet4',
        extra=dict(
            stage1=dict(
                num_modules=1,
                num_branches=1,
                block='BOTTLENECK',
                num_blocks=(4,),
                num_channels=(64,)),
            stage2=dict(
                num_modules=1,
                num_branches=2,
                block='BASIC',
                num_blocks=(4, 4),
                num_channels=(18, 36)),
            stage3=dict(
                num_modules=4,
                num_branches=3,
                block='BASIC',
                num_blocks=(4, 4, 4),
                num_channels=(18, 36, 72)),
            stage4=dict(
                num_modules=3,
                num_branches=4,
                block='BASIC',
                num_blocks=(4, 4, 4, 4),
                num_channels=(18, 36, 72, 144)))),
    neck=dict(
        type='HRFPN',
        in_channels=[18, 36, 72, 144],
        out_channels=256),
    bbox_head=dict(
        type='CenterHead',
        num_classes=80,
        in_channels=256,
        stacked_convs=1,
        feat_channels=256,
        #strides=[8, 16, 32, 64, 128],
        strides=[4, 8, 16, 32, 64],
        regress_ranges=((-1, 32),(32, 64), (64, 128), (128, 256), (256, 1e8)),
        loss_hm=dict(
            type='CenterFocalLoss'),
        loss_wh = dict(type="L1Loss",loss_weight=0.1),
        loss_offset = dict(type="L1Loss",loss_weight=1.0))
)
# training and testing settings
train_cfg = dict(
    assigner=dict(
        type='MaxIoUAssigner',
        pos_iou_thr=0.5,
        neg_iou_thr=0.4,
        min_pos_iou=0,
        ignore_iof_thr=-1),
    allowed_border=-1,
    pos_weight=-1,
    debug=False
)
test_cfg = dict(
    a = 5
    #nms_pre=1000,
    #min_bbox_size=0,
    #score_thr=0.05,
    #nms=dict(type='nms', iou_thr=0.5),
    #max_per_img=100
)
# dataset settings
dataset_type = 'CenterFPN_dataset'
data_root = '/data/lizhe/coco/'
img_norm_cfg = dict(
        mean=[0.408, 0.447, 0.470], std=[0.289, 0.274, 0.278], to_rgb=True)
data = dict(
    imgs_per_gpu=4,
    workers_per_gpu=4,
    train=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_trainval2014.json',
        img_prefix=data_root + 'images/trainval2014/',
        #img_scale=(1333, 800),
        img_scale=(800,800),
        #img_scale=(1024,1024),
        img_norm_cfg=img_norm_cfg,
        size_divisor=31,
        flip_ratio=0.5,
        with_mask=False,
        with_crowd=False,
        with_label=True),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_minival2014.json',
        img_prefix=data_root + 'images/minival2014/',
        img_scale=(1333, 800),
        img_norm_cfg=img_norm_cfg,
        size_divisor=31,
        flip_ratio=0,
        with_mask=False,
        with_crowd=False,
        with_label=True),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_minival2014.json',
        img_prefix=data_root + 'images/minival2014/',
        img_scale=(1333, 800),
        img_norm_cfg=img_norm_cfg,
        size_divisor=31,
        flip_ratio=0,
        with_mask=False,
        with_crowd=False,
        with_label=False,
        test_mode=True))
# optimizer
optimizer = dict(type='Adam', lr= 0.00025, betas=(0.9, 0.999), eps=1e-8)
    #type='SGD',
    #lr=0.01,
    #momentum=0.9,
    #weight_decay=0.0001,
    #paramwise_options=dict(bias_lr_mult=2., bias_decay_mult=0.))
optimizer_config = dict(grad_clip=None)
# learning policy
lr_config = dict(
    policy='step',
    warmup='constant',
    warmup_iters=500,
    warmup_ratio=1.0 / 3,
    step=[8, 11])
checkpoint_config = dict(interval=1)
# yapf:disable
log_config = dict(
    interval=1,
    hooks=[
        dict(type='TextLoggerHook'),
        # dict(type='TensorboardLoggerHook')
    ])
# yapf:enable
# runtime settings
total_epochs = 12
device_ids = range(8)
dist_params = dict(backend='nccl')
log_level = 'INFO'
work_dir = './work_dirs/center_fpn_r50_caffe_fpn_gn_1x_4gpu'
#load_from = 'pre_train_fpn.pth'
load_from = None
resume_from = None
workflow = [('train', 1)]
