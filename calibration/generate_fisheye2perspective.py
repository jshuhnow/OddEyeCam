import yaml
import cv2
assert cv2.__version__[0] == '3', 'The fisheye module requires opencv version >= 3.0.0'
import numpy as np
import glob

## [Constant]
img_file_name = '2'
## [Constant]


# # [Calibration]
CHECKERBOARD = (6,8)
subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC+cv2.fisheye.CALIB_CHECK_COND+cv2.fisheye.CALIB_FIX_SKEW
objp = np.zeros((1, CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
_img_shape = None
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.
images = glob.glob('./checkerboard_img/*.jpg')
for fname in images:
    img = cv2.imread(fname)
    if _img_shape == None:
        _img_shape = img.shape[:2]
    else:
        assert _img_shape == img.shape[:2], "All images must share the same size."
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    cv2.waitKey(0)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_FAST_CHECK+cv2.CALIB_CB_NORMALIZE_IMAGE)
    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        cv2.cornerSubPix(gray,corners,(3,3),(-1,-1),subpix_criteria)
        imgpoints.append(corners)
N_OK = len(objpoints)
K = np.zeros((3, 3))
D = np.zeros((4, 1))
rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
rms, _, _, _, _ = \
    cv2.fisheye.calibrate(
        objpoints,
        imgpoints,
        gray.shape[::-1],
        K,
        D,
        rvecs,
        tvecs,
        calibration_flags,
        (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
    )
print("Found " + str(N_OK) + " valid images for calibration")
print("DIM=" + str(_img_shape[::-1]))
print("K=np.array(" + str(K.tolist()) + ")")
print("D=np.array(" + str(D.tolist()) + ")")
DIM=_img_shape[::-1]
balance=1
dim2=None
dim3=None

dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort
assert dim1[0]/dim1[1] == DIM[0]/DIM[1], "Image to undistort needs to have same aspect ratio as the ones used in calibration"
if not dim2:
    dim2 = dim1
if not dim3:
    dim3 = dim1
scaled_K = K * dim1[0] / DIM[0]  # The values of K is to scale with image dimension.
scaled_K[2][2] = 1.0  # Except that K[2][2] is always 1.0
    # This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, dim2, np.eye(3), balance=1)

data = {'dim1': dim1, 
        'dim2':dim2,
        'dim3': dim3,
        'K': np.asarray(K).tolist(), 
        'D':np.asarray(D).tolist(),
        'new_K':np.asarray(new_K).tolist(),
        'scaled_K':np.asarray(scaled_K).tolist(),
        'balance':balance}

import json
with open("./parameters/pinhole_model_intrinsic.json", "w") as f:
    json.dump(data, f)
# # [Calibration]


## [Load]
import json
json_data=open("./parameters/pinhole_model_intrinsic.json").read()
data = json.loads(json_data)
scaled_K, D, new_K, dim3 = np.asarray(data['scaled_K']), np.asarray(data['D']), np.asarray(data['new_K']), tuple(data['dim3'])
## [Load]

## [Apply Perspective Projection]
filepath = "./checkerboard_img/"+img_file_name+".jpg"
# filepath = "depth_cam_img/fisheye.jpg"
Knew = scaled_K.copy()
new_K[(0,1), (0,1)] = 2 * Knew[(0,1), (0,1)]
map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), scaled_K, dim3, cv2.CV_16SC2)
img = cv2.imread(filepath)
u,v = map1[:,:,0].astype(np.float32), map1[:,:,1].astype(np.float32)
undistorted_img = cv2.remap(img, u, v, cv2.INTER_LINEAR)
undistorted_img = cv2.resize(undistorted_img,(640, 480))
img2 = cv2.imread(filepath)
cv2.imshow("fisheye (input)", img2)
cv2.imshow("fisheye2perspective result", undistorted_img)
cv2.imwrite("output/fisheye2perspective_result.jpg",undistorted_img)

# Save perspective projection map
np.savetxt("parameters/per_u.csv", u, delimiter=',')
np.savetxt("parameters/per_v.csv", v, delimiter=',')

# Generate and Save reverse perspective projection map
u_rev, v_rev = np.zeros(u.shape),np.zeros(v.shape)
i,j=0,0
for u_row,v_row in zip(u.astype(np.int), v.astype(np.int)):
    j = 0
    for u_,v_ in zip(u_row,v_row):
        if(v_>=u.shape[0] or u_>=u.shape[1]):
            continue
        u_rev[v_,u_] = j
        v_rev[v_,u_] = i
        j = j+1
    i = i+1
np.savetxt("./parameters/per_u_rev.csv",u_rev,delimiter=',')
np.savetxt("./parameters/per_v_rev.csv",v_rev,delimiter=',')

cv2.waitKey(0)
cv2.destroyAllWindows()
## [Apply Perspective Projection]