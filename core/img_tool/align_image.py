from __future__ import print_function
import cv2
import numpy as np
import argparse
from math import sqrt

###################################
##  Align equirectangular image  ##
##    (Get homography matrix)    ##
###################################

## [load]
# left_img_file = './captured_img/3264x2448_fisheye/640x480_equi/left_infinite_feature_10_result.jpg'
# right_img_file = './captured_img/3264x2448_fisheye/640x480_equi/right_infinite_feature_10_result.jpg'
left_img_file = "./captured_img/d415_RGB_15.jpg"
right_img_file = "./captured_img/perspective_15.jpg"
img1 = cv2.imread(right_img_file) # source
img2 = cv2.imread(left_img_file) # destination
# './sample/graf1.png'
# './sample/graf3.png'
if img1 is None or img2 is None:
    print('Could not open or find the images!')
    exit(0)
## [load]

## [AKAZE]
akaze = cv2.AKAZE_create()
kpts1, desc1 = akaze.detectAndCompute(img1, None)
kpts2, desc2 = akaze.detectAndCompute(img2, None)
## [AKAZE]

## [2-nn matching]
matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_BRUTEFORCE_HAMMING)
nn_matches = matcher.knnMatch(desc1, desc2, 2)
## [2-nn matching]

## [ratio test filtering]
matched1 = []
matched2 = []
nn_match_ratio = 0.8 # Nearest neighbor matching ratio
for m, n in nn_matches:
    if m.distance < nn_match_ratio * n.distance:
        matched1.append(kpts1[m.queryIdx])
        matched2.append(kpts2[m.trainIdx])
## [ratio test filtering]

## [calculate homography matrix]
src_pts = np.float32([ m.pt for m in matched1 ]).reshape(-1,1,2)
dst_pts = np.float32([ m.pt for m in matched2 ]).reshape(-1,1,2)
homography, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC) # Is least-square method applied?
print(homography)
# print(dst_pts[:,:,0].astype(np.int)) # x position
## [calculate homography matrix]

## [save image]
img_transed = cv2.warpPerspective(img1, homography, (img2.shape[1],img2.shape[0]))
cv2.imwrite('./output/result_projective_transformation.jpg',img_transed)
print("A transformed image is saved in \"output\" folder")
# cv2.imshow('result', img_transed)
# cv2.waitKey()
## [save image]

#################################
##        Check mapping        ##
##  (Check homography matrix)  ##
#################################

# ## [load]
# fs = cv2.FileStorage("./parameters/homography_m.xml", cv2.FILE_STORAGE_READ)
# homography = fs.getFirstTopLevelNode().mat()
# ## [load]

## [homography check]
inliers1 = []
inliers2 = []
good_matches = []
inlier_threshold = 2.5 # Distance threshold to identify inliers with homography check
for i, m in enumerate(matched1):
    col = np.ones((3,1), dtype=np.float64)
    col[0:2,0] = m.pt

    col = np.dot(homography, col)
    col /= col[2,0]
    dist = sqrt(pow(col[0,0] - matched2[i].pt[0], 2) +\
                pow(col[1,0] - matched2[i].pt[1], 2))

    if dist < inlier_threshold:
        good_matches.append(cv2.DMatch(len(inliers1), len(inliers2), 0))
        inliers1.append(matched1[i])
        inliers2.append(matched2[i])
## [homography check]

## [draw final matches]
res = np.empty((max(img1.shape[0], img2.shape[0]), img1.shape[1]+img2.shape[1], 3), dtype=np.uint8)
cv2.drawMatches(img1, inliers1, img2, inliers2, good_matches, res)
cv2.imwrite("akaze_result.png", res)

inlier_ratio = len(inliers1) / float(len(matched1))
print('A-KAZE Matching Results')
print('*******************************')
print('# Keypoints 1:                        \t', len(kpts1))
print('# Keypoints 2:                        \t', len(kpts2))
print('# Matches:                            \t', len(matched1))
print('# Inliers:                            \t', len(inliers1))
print('# Inliers Ratio:                      \t', inlier_ratio)

cv2.imshow('result', res)
cv2.imwrite('./result_AKAZE.jpg',res)
cv2.waitKey()
## [draw final matches]